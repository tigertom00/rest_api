import jwt
import requests
import os
from django.conf import settings
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
load_dotenv(settings.BASE_DIR / '.env')




CLERK_JWT_ISSUER = os.getenv('CLERK_URL')
CLERK_JWT_PUBLIC_KEY_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"

class ClerkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        User = get_user_model()
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            # Fetch Clerk's public keys
            jwks = requests.get(CLERK_JWT_PUBLIC_KEY_URL).json()
            # (You may want to cache this in production)
            public_keys = {key['kid']: jwt.algorithms.RSAAlgorithm.from_jwk(key) for key in jwks['keys']}
            unverified_header = jwt.get_unverified_header(token)
            key = public_keys[unverified_header['kid']]
            payload = jwt.decode(token, key=key, algorithms=['RS256'], audience=settings.CLERK_JWT_AUDIENCE)
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid Clerk token')

        # Get or create user
        email = payload.get('email')
        if not email:
            raise exceptions.AuthenticationFailed('No email in Clerk token')
        user, _ = User.objects.get_or_create(email=email, defaults={'username': email})
        return (user, None)