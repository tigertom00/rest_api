from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from django.contrib.auth import get_user_model
from .serializers import UsersSerializer, CreateUsersSerializer, BlacklistTokenSerializer
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import hmac
import hashlib
import base64
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

#* Clerk Webhook View

@csrf_exempt
def clerk_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    signature = request.headers.get("Clerk-Signature")
    if not signature:
        return HttpResponse("Missing signature", status=400)

    secret = settings.CLERK_WEBHOOK_SECRET.encode()
    body = request.body

    # Compute the expected signature as bytes
    expected_signature = hmac.new(secret, body, hashlib.sha256).digest()

    # Decode the signature from base64 to bytes
    try:
        received_signature = base64.b64decode(signature)
    except Exception:
        return HttpResponse("Invalid signature encoding", status=400)

    # Use compare_digest for constant-time comparison
    if not hmac.compare_digest(received_signature, expected_signature):
        return HttpResponse("Invalid signature", status=400)

    event = json.loads(body)
    event_type = event.get("type")
    data = event.get("data", {})

    # Handle the event based on its type
    # Here’s how you can handle Clerk webhook events for user creation and deletion, using Django’s ORM. This example assumes your user model uses email as a unique identifier (as is common with Clerk).
    if event_type == "user.created":
        email = data.get("email_addresses", [{}])[0].get("email_address")
        username = data.get("username") or email
        if email:
            User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "is_active": True,
                }
            )
    elif event_type == "user.updated":
        email = data.get("email_addresses", [{}])[0].get("email_address")
        username = data.get("username") or email
        if email:
            User.objects.filter(email=email).update(username=username)
    elif event_type == "user.deleted":
        email = data.get("email_addresses", [{}])[0].get("email_address")
        if email:
            try:
                user = User.objects.get(email=email)
                user.delete()
            except User.DoesNotExist:
                pass
    elif event_type == "user.get":
        # Usually, Clerk does not send a "get" event via webhook.
        # If you want to handle a custom event, you can implement logic here.
        pass
    # Add more event types as needed

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