from rest_framework import viewsets, permissions, status, generics
from django.contrib.auth import get_user_model
from .serializers import UsersSerializer, CreateUsersSerializer, BlacklistTokenSerializer
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from svix.webhooks import Webhook, WebhookVerificationError
from .models import UserEmail, UserPhone
from datetime import datetime, timezone

User = get_user_model()

class ClerkAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'restAPI.clerk.ClerkAuthentication'  # full import path
    name = 'ClerkAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }

#* Clerk Webhook View

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
    username = data.get("username") or (email.split('@')[0] if email else None)
    clerk_id = data.get("id")
    clerk_profile_image_url = data.get("profile_image_url")
    two_factor_enabled = data.get("two_factor_enabled", False)
    has_image = bool(clerk_profile_image_url)
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    phone_numbers = data.get("phone_numbers", [])
    email_list = data.get("email_addresses", [])
    clerk_updated_at = data.get("updated_at")
    if clerk_updated_at:
        try:
            clerk_updated_at = datetime.fromtimestamp(clerk_updated_at / 1000, tz=timezone.utc)
        except Exception:
            clerk_updated_at = None

    display_name = (first_name or username or "").capitalize()

    if event_type in ("user.created", "user.updated"):
        if not email:
            return JsonResponse({"status": "error", "detail": "No email provided"}, status=400)

        user_obj, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "display_name": display_name,
                "clerk_id": clerk_id,
                "clerk_profile_image_url": clerk_profile_image_url,
                "two_factor_enabled": two_factor_enabled,
                "has_image": has_image,
                "is_active": True,
                "first_name": first_name,
                "last_name": last_name,
                "clerk_updated_at": clerk_updated_at,
            }
        )
        if not created:
            # Update fields if user already exists
            User.objects.filter(email=email).update(
                username=username,
                display_name=display_name,
                clerk_id=clerk_id,
                clerk_profile_image_url=clerk_profile_image_url,
                two_factor_enabled=two_factor_enabled,
                has_image=has_image,
                first_name=first_name,
                last_name=last_name,
                clerk_updated_at=clerk_updated_at,
            )

        # --- Sync phones ---
        clerk_phones = {phone.get("phone_number") for phone in phone_numbers if phone.get("phone_number")}
        # Remove phones not in Clerk
        UserPhone.objects.filter(user=user_obj).exclude(phone_nr__in=clerk_phones).delete()
        for phone in phone_numbers:
            phone_nr = phone.get("phone_number")
            if not phone_nr:
                continue
            UserPhone.objects.update_or_create(
                user=user_obj,
                phone_nr=phone_nr,
                defaults={
                    "is_primary": phone.get("primary", False),
                    "is_verified": phone.get("verification", {}).get("status") == "verified"
                }
            )

        # --- Sync emails ---
        clerk_emails = {email_data.get("email_address") for email_data in email_list if email_data.get("email_address")}
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
                    "is_verified": email_data.get("verification", {}).get("status") == "verified"
                }
            )

    elif event_type == "user.deleted":
        if email:
            try:
                user = User.objects.get(email=email)
                user.delete()
            except User.DoesNotExist:
                pass

    return JsonResponse({"status": "ok"})

#* Index view for the API
def index(request):
    return HttpResponse("Welcome to the REST API!")

#* Create Users ViewSet
class CreateUsersViewSet(generics.CreateAPIView):
    serializer_class = CreateUsersSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()


#* Users ViewSet
class UsersViewSet(viewsets.ModelViewSet):

    serializer_class = UsersSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]
    queryset = User.objects.all()

    def get_queryset(self):

        return self.queryset.filter(username=self.request.user)

    def perform_create(self, serializer):
        serializer.save(username=self.request.user)

#* Blacklist Token View
class BlacklistTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlacklistTokenSerializer

    def post(self, request,):
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