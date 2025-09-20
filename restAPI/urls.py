from django.urls import path, include
from rest_framework import routers
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = routers.DefaultRouter()
router.register('api/user', views.UsersViewSet, 'users')

urlpatterns = [
    #path('', views.index, name='index'),
    path("", views.landing_page, name="landing"),
    path('auth/register/' , views.CreateUsersViewSet.as_view(), name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/token/blacklist/', views.BlacklistTokenView.as_view(), name='blacklist_token'),
    path('auth/o/', include('oauth2_provider.urls', namespace='oauth2_provider')),  # OAuth2 endpoints
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('clerk/webhook/', views.clerk_webhook, name='clerk_webhook'),
    path('api/', include('mcp_server.urls')),  # MCP server endpoints
    path('api/', include('app.docker_monitor.urls')),  # Docker monitoring endpoints
    
]
urlpatterns += router.urls