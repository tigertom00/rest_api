from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            # Verify the JWT token with Clerk's public key
            # You'll need to implement this based on Clerk's documentation
            decoded_token = jwt.decode(
                token,
                settings.CLERK_PUBLIC_KEY,
                algorithms=['RS256'],
                audience=['audience']
            )
            
            # Get the Clerk user ID from the token
            clerk_user_id = decoded_token.get('sub')
            if not clerk_user_id:
                raise AuthenticationFailed('Invalid token')
                
            # Find the user by clerk_id
            try:
                user = User.objects.get(clerk_id=clerk_user_id)
                return (user, None)
            except User.DoesNotExist:
                # Optionally create user here or raise AuthenticationFailed
                raise AuthenticationFailed('User not found')
                
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')