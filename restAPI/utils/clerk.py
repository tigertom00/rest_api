import jwt, requests
from django.conf import settings
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model

class ClerkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        User = get_user_model()
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        try:
            jwks = requests.get(settings.CLERK_JWT_PUBLIC_KEY_URL).json()
            public_keys = {key['kid']: jwt.algorithms.RSAAlgorithm.from_jwk(key) for key in jwks['keys']}
            unverified_header = jwt.get_unverified_header(token)
            key = public_keys[unverified_header['kid']]
            payload = jwt.decode(token, key=key, algorithms=['RS256'], audience=settings.CLERK_URL if 'aud' in jwt.decode(token, options={"verify_signature": False}) else None)
        except Exception as e:
            return None
        user_id = payload.get('sub')        
        if not user_id:
            raise exceptions.AuthenticationFailed('No sub in Clerk token')
        user, _ = User.objects.get_or_create(clerk_user_id=user_id, defaults={'username': user_id})
        return (user, None)