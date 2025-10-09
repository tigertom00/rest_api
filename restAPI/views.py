from datetime import UTC, datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import (
    action,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from svix.webhooks import Webhook, WebhookVerificationError

from .models import UserDevice, UserEmail, UserPhone
from .serializers import (
    AdminPasswordResetSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    BlacklistTokenSerializer,
    CreateUsersSerializer,
    MobileAuthResponseSerializer,
    UserBasicSerializer,
    UserDeviceCreateSerializer,
    UserDeviceSerializer,
    UserDeviceUpdateSerializer,
    UsersSerializer,
)
from .utils.audit import AuditLogger, sensitive_operation
from .utils.throttling import AdminRateThrottle

User = get_user_model()


class ClerkAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "restAPI.utils.clerk.ClerkAuthentication"  # full import path
    name = "ClerkAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


# * Clerk Webhook View


@csrf_exempt
def clerk_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    secret = settings.CLERK_WEBHOOK_KEY
    headers = request.headers
    body = request.body

    wh = Webhook(secret)
    try:
        event = wh.verify(body, headers)
    except WebhookVerificationError:
        return HttpResponse("Invalid signature", status=400)

    event_type = event.get("type")
    data = event.get("data", {})

    # Extract Clerk fields
    email = data.get("email_addresses", [{}])[0].get("email_address")
    username = data.get("username") or (email.split("@")[0] if email else None)
    clerk_user_id = data.get("id")
    clerk_profile_image_url = data.get("profile_image_url")
    two_factor_enabled = data.get("two_factor_enabled", False)
    has_image = bool(clerk_profile_image_url)
    first_name = data.get("first_name") or ""
    last_name = data.get("last_name") or ""
    phone_numbers = data.get("phone_numbers", [])
    email_list = data.get("email_addresses", [])
    clerk_updated_at = data.get("updated_at")
    if clerk_updated_at:
        try:
            clerk_updated_at = datetime.fromtimestamp(clerk_updated_at / 1000, tz=UTC)
        except Exception:
            clerk_updated_at = None

    display_name = (first_name or username or "").capitalize()

    if event_type in ("user.created", "user.updated"):
        if not email:
            return JsonResponse(
                {"status": "error", "detail": "No email provided"}, status=400
            )

        user_obj, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "display_name": display_name,
                "clerk_user_id": clerk_user_id,
                "clerk_profile_image_url": clerk_profile_image_url,
                "two_factor_enabled": two_factor_enabled,
                "has_image": has_image,
                "is_active": True,
                "first_name": first_name,
                "last_name": last_name,
                "clerk_updated_at": clerk_updated_at,
            },
        )
        if not created:
            # Update fields if user already exists
            User.objects.filter(email=email).update(
                username=username,
                display_name=display_name,
                clerk_user_id=clerk_user_id,
                clerk_profile_image_url=clerk_profile_image_url,
                two_factor_enabled=two_factor_enabled,
                has_image=has_image,
                first_name=first_name,
                last_name=last_name,
                clerk_updated_at=clerk_updated_at,
            )

        # --- Sync phones ---
        clerk_phones = {
            phone.get("phone_number")
            for phone in phone_numbers
            if phone.get("phone_number")
        }
        # Remove phones not in Clerk
        UserPhone.objects.filter(user=user_obj).exclude(
            phone_nr__in=clerk_phones
        ).delete()
        for phone in phone_numbers:
            phone_nr = phone.get("phone_number")
            if not phone_nr:
                continue
            UserPhone.objects.update_or_create(
                user=user_obj,
                phone_nr=phone_nr,
                defaults={
                    "is_primary": phone.get("primary", False),
                    "is_verified": phone.get("verification", {}).get("status")
                    == "verified",
                },
            )

        # --- Sync emails ---
        clerk_emails = {
            email_data.get("email_address")
            for email_data in email_list
            if email_data.get("email_address")
        }
        UserEmail.objects.filter(user=user_obj).exclude(email__in=clerk_emails).delete()
        for email_data in email_list:
            email_addr = email_data.get("email_address")
            if not email_addr:
                continue
            UserEmail.objects.update_or_create(
                user=user_obj,
                email=email_addr,
                defaults={
                    "is_primary": email_data.get("primary", False),
                    "is_verified": (email_data.get("verification") or {}).get("status")
                    == "verified",
                },
            )

    elif event_type == "user.deleted":
        if email:
            try:
                user = User.objects.get(email=email)
                user.delete()
            except User.DoesNotExist:
                pass

    return JsonResponse({"status": "ok"})


# * Index view for the API
def index(request):
    return HttpResponse("Welcome to the REST API!")


# * Create Users ViewSet
class CreateUsersViewSet(generics.CreateAPIView):
    serializer_class = CreateUsersSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()


# * Users ViewSet
class UsersViewSet(viewsets.ModelViewSet):

    serializer_class = UsersSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_queryset(self):

        return self.queryset.filter(id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(username=self.request.user)


# * Blacklist Token View
class BlacklistTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlacklistTokenSerializer

    def post(
        self,
        request,
    ):
        serializer = BlacklistTokenSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = request.data["refresh_token"]
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(status=status.HTTP_202_ACCEPTED)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# * Mobile Authentication View
class MobileAuthView(APIView):
    """
    Mobile-specific authentication endpoint that combines login + device registration.
    Returns JWT tokens, user info, and device_id in a single response.

    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "device_type": "ios",
        "device_name": "iPhone 15",
        "device_id": "unique-device-identifier",
        "push_token": "ExponentPushToken[...]",
        "os_version": "17.2",
        "app_version": "1.0.0"
    }
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"},
                    "device_type": {"type": "string"},
                    "device_name": {"type": "string"},
                    "device_id": {"type": "string"},
                    "push_token": {"type": "string"},
                    "os_version": {"type": "string"},
                    "app_version": {"type": "string"},
                },
                "required": ["email", "password", "device_type"],
            }
        },
        responses={
            200: MobileAuthResponseSerializer,
            401: {"description": "Invalid credentials"},
            400: {"description": "Missing required fields"},
        },
    )
    def post(self, request):
        from django.contrib.auth import authenticate

        # Extract credentials
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        lifetime = int(refresh.access_token.lifetime.total_seconds())

        # Extract device information
        device_data = {
            "device_type": request.data.get("device_type"),
            "device_name": request.data.get("device_name", ""),
            "device_id": request.data.get("device_id"),
            "push_token": request.data.get("push_token"),
            "os_version": request.data.get("os_version", ""),
            "app_version": request.data.get("app_version", ""),
        }

        # Get IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0]
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        device_data["ip_address"] = ip_address

        # Create or update device
        device = None
        if device_data.get("device_id"):
            # Try to find existing device
            device = UserDevice.objects.filter(
                user=user, device_id=device_data["device_id"]
            ).first()

        if device:
            # Update existing device
            for key, value in device_data.items():
                if value:  # Only update non-empty values
                    setattr(device, key, value)
            device.is_active = True
            device.save()
        else:
            # Create new device
            device = UserDevice.objects.create(user=user, **device_data)

        # Log the login
        AuditLogger.log_user_action(
            "LOGIN",
            "MobileAuth",
            user,
            request,
            f"Mobile login from {device.get_device_type_display()}",
        )

        # Serialize user data
        user_serializer = UserBasicSerializer(user)

        # Return combined response
        return Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "lifetime": lifetime,
                "device_id": str(device.id),
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only ViewSet for user management.
    Provides endpoints for listing, updating, and managing users.
    """

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "username", "first_name", "last_name", "display_name"]
    ordering_fields = ["date_joined", "last_login", "email"]
    ordering = ["-date_joined"]
    throttle_classes = [AdminRateThrottle]

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def get_queryset(self):
        queryset = User.objects.all()

        # Filter by registration date range
        date_start = self.request.query_params.get("registration_date_start")
        date_end = self.request.query_params.get("registration_date_end")

        if date_start:
            try:
                from datetime import datetime

                start_date = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
                queryset = queryset.filter(date_joined__gte=start_date)
            except ValueError:
                pass  # Invalid date format, ignore filter

        if date_end:
            try:
                from datetime import datetime

                end_date = datetime.fromisoformat(date_end.replace("Z", "+00:00"))
                queryset = queryset.filter(date_joined__lte=end_date)
            except ValueError:
                pass  # Invalid date format, ignore filter

        return queryset.select_related()

    @extend_schema(
        request=AdminPasswordResetSerializer,
        responses={
            200: {"description": "Password reset successfully"},
            400: {"description": "Invalid password"},
            404: {"description": "User not found"},
        },
    )
    @sensitive_operation("User", severity="CRITICAL")
    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        """
        Admin-initiated password reset.

        Request body:
        {
            "new_password": "new_secure_password123"
        }
        """
        user = self.get_object()
        serializer = AdminPasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data["new_password"]
            user.set_password(new_password)
            user.save()

            # Log the admin action
            AuditLogger.log_admin_action(
                "password_reset", user, request.user, request, {"reset_by_admin": True}
            )

            return Response(
                {
                    "message": f"Password reset successfully for user {user.email}",
                    "user_id": user.id,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"is_active": {"type": "boolean"}},
            }
        },
        responses={
            200: {"description": "User status updated"},
            404: {"description": "User not found"},
        },
    )
    @action(detail=True, methods=["patch"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        """
        Toggle user active status.

        Request body:
        {
            "is_active": true/false
        }
        """
        user = self.get_object()
        is_active = request.data.get("is_active")

        if is_active is not None:
            user.is_active = is_active
            user.save()

            return Response(
                {
                    "message": f'User {user.email} {"activated" if is_active else "deactivated"}',
                    "user_id": user.id,
                    "is_active": user.is_active,
                }
            )

        return Response(
            {"error": "is_active field is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of admin users via API for safety."""
        return Response(
            {
                "error": "User deletion is not allowed through the API for security reasons"
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# Landing page view
def landing_page(request):
    return render(request, "landing.html")


# * UserDevice ViewSet for session/device management
class UserDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user devices (primarily mobile devices).
    Supports registering new devices, updating push tokens, and revoking device access.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["last_active", "created_at"]
    ordering = ["-last_active"]

    def get_queryset(self):
        # Users can only see their own devices
        return UserDevice.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return UserDeviceCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserDeviceUpdateSerializer
        return UserDeviceSerializer

    def perform_create(self, serializer):
        # User is set in the serializer's create method
        serializer.save()

    @extend_schema(
        request=None,
        responses={
            200: {"description": "Device revoked successfully"},
            404: {"description": "Device not found"},
        },
    )
    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke_device(self, request, pk=None):
        """
        Revoke access for a specific device.

        This will set is_active=False and effectively log out the device.
        """
        device = self.get_object()
        device.revoke()

        # Log the action
        AuditLogger.log_user_action(
            "LOGOUT",
            "UserDevice",
            request.user,
            request,
            f"Device {device.device_name or device.device_type} revoked",
        )

        return Response(
            {
                "message": f"Device '{device.device_name or device.get_device_type_display()}' has been revoked",
                "device_id": str(device.id),
            }
        )

    @extend_schema(
        request=None,
        responses={200: UserDeviceSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="active")
    def active_devices(self, request):
        """
        Get all active devices for the current user.
        """
        active_devices = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_devices, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses={
            200: {"description": "All devices revoked except current one"},
        },
    )
    @action(detail=False, methods=["post"], url_path="revoke-all-others")
    def revoke_all_others(self, request):
        """
        Revoke all other devices except the one making this request.

        The device_id should be provided in the request body to identify
        the current device to keep active.
        """
        current_device_id = request.data.get("current_device_id")

        if not current_device_id:
            return Response(
                {"error": "current_device_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Revoke all devices except the current one
        devices_to_revoke = (
            self.get_queryset().filter(is_active=True).exclude(id=current_device_id)
        )
        count = devices_to_revoke.count()
        devices_to_revoke.update(is_active=False)

        # Log the action
        AuditLogger.log_user_action(
            "LOGOUT",
            "UserDevice",
            request.user,
            request,
            f"Revoked {count} other devices",
        )

        return Response(
            {
                "message": f"Successfully revoked {count} device(s)",
                "revoked_count": count,
            }
        )
