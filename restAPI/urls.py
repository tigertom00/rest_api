from django.urls import path, include
from rest_framework import routers
from .views import index, clerk_webhook, UsersViewSet, BlacklistTokenView, CreateUsersViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


router = routers.DefaultRouter()
router.register('user', UsersViewSet, 'users')


urlpatterns = [
    path('', index, name='index'),
    path('register/' , CreateUsersViewSet.as_view(), name='register'),
    #path('dj-rest-auth/', include('dj_rest_auth.urls')),
    #path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', BlacklistTokenView.as_view(), name='blacklist_token'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('clerk-webhook/', clerk_webhook, name='clerk_webhook'),
]
urlpatterns += router.urls