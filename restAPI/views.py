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

from .models import UserEmail, UserPhone
from .serializers import (
    AdminPasswordResetSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    BlacklistTokenSerializer,
    CreateUsersSerializer,
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
