import email
import jwt
import requests
import os
from django.conf import settings
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model


CLERK_JWT_PUBLIC_KEY_URL = f"{settings.CLERK_URL}/.well-known/jwks.json"

class ClerkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        User = get_user_model()
        
        auth_header = request.headers.get('Authorization')
        print("Auth header:", auth_header)
        if not auth_header or not auth_header.startswith('Bearer '):
            print("No Bearer token found")
            return None

        token = auth_header.split(' ')[1]
        print("Token:", token)
        try:
            jwks = requests.get(CLERK_JWT_PUBLIC_KEY_URL).json()
            print("JWKS:", jwks)
            public_keys = {key['kid']: jwt.algorithms.RSAAlgorithm.from_jwk(key) for key in jwks['keys']}
            unverified_header = jwt.get_unverified_header(token)
            print("Unverified header:", unverified_header)
            key = public_keys[unverified_header['kid']]
            payload = jwt.decode(token, key=key, algorithms=['RS256'], audience=settings.CLERK_URL if 'aud' in jwt.decode(token, options={"verify_signature": False}) else None)
            print("Payload:", payload)
        except Exception as e:
            print("JWT decode error:", e)
            return None

        user_id = payload.get('sub')
        print("User ID from payload:", user_id)
        if not user_id:
            raise exceptions.AuthenticationFailed('No sub in Clerk token')
        user, _ = User.objects.get_or_create(clerk_user_id=user_id, defaults={'username': user_id})
        print("Authenticated user:", user)
        return (user, None)