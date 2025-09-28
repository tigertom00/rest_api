import json
import logging
from functools import wraps

from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()

# Configure audit logger
audit_logger = logging.getLogger("audit")

# Import AuditLog from models
from ..models import AuditLog


class AuditLogger:
    """
    Centralized audit logging functionality.
    """

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip or ""

    @staticmethod
    def log_action(
        action: str,
        resource: str,
        description: str,
        user: User = None,
        request: HttpRequest = None,
        resource_id: str = "",
        severity: str = AuditLog.Severity.LOW,
        metadata: dict = None,
    ):
        """
        Log an audit action.

        Args:
            action: Action type from AuditLog.ActionType
            resource: Resource type (e.g., 'Task', 'User')
            description: Human-readable description
            user: User who performed the action
            request: HTTP request object
            resource_id: ID of the affected resource
            severity: Severity level
            metadata: Additional context data
        """
        try:
            # Extract request information
            ip_address = ""
            user_agent = ""
            request_method = ""
            request_path = ""

            if request:
                ip_address = AuditLogger.get_client_ip(request)
                user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
                request_method = request.method
                request_path = request.path[:500]

            # Create audit log entry
            audit_entry = AuditLog.objects.create(
                user=user,
                user_email=user.email if user else "",
                action=action,
                resource=resource,
                resource_id=str(resource_id),
                description=description,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                metadata=metadata or {},
            )

            # Also log to file/external system
            audit_logger.info(
                f"AUDIT: {action} | {resource}:{resource_id} | "
                f"User: {user.email if user else 'Anonymous'} | "
                f"IP: {ip_address} | Description: {description}",
                extra={
                    "audit_id": audit_entry.id,
                    "action": action,
                    "resource": resource,
                    "resource_id": resource_id,
                    "user_id": user.id if user else None,
                    "user_email": user.email if user else "",
                    "ip_address": ip_address,
                    "severity": severity,
                    "metadata": metadata or {},
                },
            )

        except Exception as e:
            # Never let audit logging break the main functionality
            audit_logger.error(f"Failed to create audit log: {e}")

    @staticmethod
    def log_login(user: User, request: HttpRequest, success: bool = True):
        """Log user login attempts."""
        action = AuditLog.ActionType.LOGIN
        severity = AuditLog.Severity.LOW if success else AuditLog.Severity.MEDIUM
        description = f"User login {'successful' if success else 'failed'}"

        if not success:
            action = AuditLog.ActionType.ACCESS_DENIED
            description = "Failed login attempt"

        AuditLogger.log_action(
            action=action,
            resource="Authentication",
            description=description,
            user=user if success else None,
            request=request,
            severity=severity,
            metadata={"login_success": success},
        )

    @staticmethod
    def log_admin_action(
        action: str,
        target_user: User,
        admin_user: User,
        request: HttpRequest,
        details: dict = None,
    ):
        """Log administrative actions on users."""
        AuditLogger.log_action(
            action=AuditLog.ActionType.ADMIN_ACTION,
            resource="User",
            resource_id=target_user.id,
            description=f"Admin {action} on user {target_user.email}",
            user=admin_user,
            request=request,
            severity=AuditLog.Severity.HIGH,
            metadata={
                "admin_action": action,
                "target_user_email": target_user.email,
                "details": details or {},
            },
        )

    @staticmethod
    def log_bulk_operation(
        operation: str,
        count: int,
        user: User,
        request: HttpRequest,
        resource_type: str = "Task",
    ):
        """Log bulk operations."""
        AuditLogger.log_action(
            action=AuditLog.ActionType.BULK_OPERATION,
            resource=resource_type,
            description=f"Bulk {operation} on {count} {resource_type.lower()}s",
            user=user,
            request=request,
            severity=AuditLog.Severity.MEDIUM,
            metadata={
                "bulk_operation": operation,
                "affected_count": count,
                "resource_type": resource_type,
            },
        )

    @staticmethod
    def log_file_operation(
        action: str, filename: str, user: User, request: HttpRequest, file_size: int = 0
    ):
        """Log file upload/download operations."""
        AuditLogger.log_action(
            action=AuditLog.ActionType.FILE_UPLOAD,
            resource="File",
            description=f"File {action}: {filename}",
            user=user,
            request=request,
            severity=AuditLog.Severity.LOW,
            metadata={
                "file_action": action,
                "filename": filename,
                "file_size": file_size,
            },
        )

    @staticmethod
    def log_permission_change(
        target_user: User, changes: dict, admin_user: User, request: HttpRequest
    ):
        """Log permission and role changes."""
        AuditLogger.log_action(
            action=AuditLog.ActionType.PERMISSION_CHANGE,
            resource="User",
            resource_id=target_user.id,
            description=f"Permission changes for {target_user.email}: {json.dumps(changes)}",
            user=admin_user,
            request=request,
            severity=AuditLog.Severity.HIGH,
            metadata={
                "target_user_email": target_user.email,
                "permission_changes": changes,
            },
        )

    @staticmethod
    def log_data_access(
        resource: str,
        resource_id: str,
        user: User,
        request: HttpRequest,
        action: str = "READ",
    ):
        """Log access to sensitive data."""
        severity = AuditLog.Severity.LOW
        if action in ["UPDATE", "DELETE"]:
            severity = AuditLog.Severity.MEDIUM

        AuditLogger.log_action(
            action=action,
            resource=resource,
            resource_id=resource_id,
            description=f"Data {action.lower()} on {resource}:{resource_id}",
            user=user,
            request=request,
            severity=severity,
        )


def audit_action(
    action: str,
    resource: str,
    severity: str = AuditLog.Severity.LOW,
    description_template: str = None,
):
    """
    Decorator for automatically auditing view actions.

    Args:
        action: Action type from AuditLog.ActionType
        resource: Resource type being acted upon
        severity: Severity level
        description_template: Template for description (can use {action}, {resource}, etc.)

    Usage:
        @audit_action('CREATE', 'Task', severity='MEDIUM')
        def create_task(self, request):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Execute the original function
            response = func(self, request, *args, **kwargs)

            # Log the action if successful (2xx status codes)
            if hasattr(response, "status_code") and 200 <= response.status_code < 300:
                description = description_template or f"{action} {resource}"
                resource_id = kwargs.get("pk", "")

                AuditLogger.log_action(
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    description=description,
                    user=getattr(request, "user", None),
                    request=request,
                    severity=severity,
                )

            return response

        return wrapper

    return decorator


def sensitive_operation(resource: str, severity: str = AuditLog.Severity.HIGH):
    """
    Decorator for marking and auditing sensitive operations.

    Usage:
        @sensitive_operation('User', severity='CRITICAL')
        def reset_password(self, request, pk=None):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Log access attempt
            resource_id = kwargs.get("pk", "")
            AuditLogger.log_action(
                action="ACCESS_ATTEMPT",
                resource=resource,
                resource_id=resource_id,
                description=f"Sensitive operation attempted: {func.__name__}",
                user=getattr(request, "user", None),
                request=request,
                severity=AuditLog.Severity.MEDIUM,
            )

            # Execute the original function
            response = func(self, request, *args, **kwargs)

            # Log the result
            if hasattr(response, "status_code"):
                if 200 <= response.status_code < 300:
                    action_type = "SENSITIVE_OPERATION_SUCCESS"
                    description = f"Sensitive operation successful: {func.__name__}"
                    log_severity = severity
                else:
                    action_type = "SENSITIVE_OPERATION_FAILED"
                    description = f"Sensitive operation failed: {func.__name__}"
                    log_severity = AuditLog.Severity.CRITICAL

                AuditLogger.log_action(
                    action=action_type,
                    resource=resource,
                    resource_id=resource_id,
                    description=description,
                    user=getattr(request, "user", None),
                    request=request,
                    severity=log_severity,
                    metadata={
                        "operation": func.__name__,
                        "status_code": response.status_code,
                    },
                )

            return response

        return wrapper

    return decorator
