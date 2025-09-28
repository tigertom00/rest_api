import uuid
from datetime import datetime

from django.core.exceptions import (
    PermissionDenied,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.

    Expected format:
    {
        "error": {
            "code": "string",
            "message": "string",
            "details": "any",
            "field_errors": {
                "field": ["error1", "error2"]
            }
        },
        "timestamp": "ISO string",
        "request_id": "UUID string"
    }
    """

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Generate request ID for debugging
    request_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    if response is not None:
        custom_response_data = {
            "error": {
                "code": get_error_code(exc, response.status_code),
                "message": get_error_message(exc, response.data),
                "details": get_error_details(exc, response.data),
            },
            "timestamp": timestamp,
            "request_id": request_id,
        }

        # Add field-level errors for validation errors
        field_errors = get_field_errors(response.data)
        if field_errors:
            custom_response_data["error"]["field_errors"] = field_errors

        response.data = custom_response_data

    else:
        # Handle exceptions not caught by DRF
        if isinstance(exc, Http404):
            custom_response_data = {
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": str(exc),
                },
                "timestamp": timestamp,
                "request_id": request_id,
            }
            response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)

        elif isinstance(exc, PermissionDenied):
            custom_response_data = {
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "You do not have permission to perform this action.",
                    "details": str(exc),
                },
                "timestamp": timestamp,
                "request_id": request_id,
            }
            response = Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)

        elif isinstance(exc, DjangoValidationError):
            custom_response_data = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The provided data is invalid.",
                    "details": str(exc),
                },
                "timestamp": timestamp,
                "request_id": request_id,
            }
            response = Response(
                custom_response_data, status=status.HTTP_400_BAD_REQUEST
            )

    return response


def get_error_code(exc, status_code):
    """Generate appropriate error code based on exception type and status code."""

    # Map exception types to error codes
    if hasattr(exc, "__class__"):
        exc_name = exc.__class__.__name__

        if exc_name == "ValidationError":
            return "VALIDATION_ERROR"
        elif exc_name == "AuthenticationFailed":
            return "AUTHENTICATION_FAILED"
        elif exc_name == "NotAuthenticated":
            return "AUTHENTICATION_REQUIRED"
        elif exc_name == "PermissionDenied":
            return "PERMISSION_DENIED"
        elif exc_name == "NotFound" or exc_name == "Http404":
            return "RESOURCE_NOT_FOUND"
        elif exc_name == "MethodNotAllowed":
            return "METHOD_NOT_ALLOWED"
        elif exc_name == "NotAcceptable":
            return "NOT_ACCEPTABLE"
        elif exc_name == "UnsupportedMediaType":
            return "UNSUPPORTED_MEDIA_TYPE"
        elif exc_name == "Throttled":
            return "RATE_LIMIT_EXCEEDED"

    # Map status codes to error codes
    status_code_mapping = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }

    return status_code_mapping.get(status_code, "UNKNOWN_ERROR")


def get_error_message(exc, response_data):
    """Generate user-friendly error message."""

    # Handle DRF validation errors
    if isinstance(response_data, dict):
        if "detail" in response_data:
            return str(response_data["detail"])
        elif "non_field_errors" in response_data:
            errors = response_data["non_field_errors"]
            if isinstance(errors, list) and errors:
                return str(errors[0])

    # Handle list of errors
    if isinstance(response_data, list) and response_data:
        return str(response_data[0])

    # Fallback to exception message
    if hasattr(exc, "detail"):
        return str(exc.detail)

    return str(exc)


def get_error_details(exc, response_data):
    """Extract additional error details."""

    # For validation errors, return the full error structure
    if hasattr(exc, "__class__") and exc.__class__.__name__ == "ValidationError":
        return response_data

    # For other errors, return the exception details
    return str(exc) if exc else None


def get_field_errors(response_data):
    """Extract field-level validation errors."""

    if not isinstance(response_data, dict):
        return None

    field_errors = {}

    for field, errors in response_data.items():
        if field not in ["detail", "non_field_errors"]:
            if isinstance(errors, list):
                field_errors[field] = [str(error) for error in errors]
            else:
                field_errors[field] = [str(errors)]

    return field_errors if field_errors else None
