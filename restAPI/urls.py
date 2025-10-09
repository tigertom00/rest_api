from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views
from .utils.monitoring import health_check, metrics_endpoint

router = routers.DefaultRouter()
router.register("api/user", views.UsersViewSet, "users")
router.register("api/admin/users", views.AdminUserViewSet, "admin-users")
router.register("api/devices", views.UserDeviceViewSet, "devices")

urlpatterns = [
    # path('', views.index, name='index'),
    path("", views.landing_page, name="landing"),
    path("auth/register/", views.CreateUsersViewSet.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path(
        "auth/token/blacklist/",
        views.BlacklistTokenView.as_view(),
        name="blacklist_token",
    ),
    path(
        "auth/mobile/login/",
        views.MobileAuthView.as_view(),
        name="mobile_auth",
    ),
    path(
        "auth/o/", include("oauth2_provider.urls", namespace="oauth2_provider")
    ),  # OAuth2 endpoints
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("clerk/webhook/", views.clerk_webhook, name="clerk_webhook"),
    path("api/", include("mcp_server.urls")),  # MCP server endpoints
    path("api/", include("app.docker_monitor.urls")),  # Docker monitoring endpoints
    path(
        "api/admin/metrics/", metrics_endpoint, name="admin_metrics"
    ),  # Performance metrics endpoint
    path("api/health/", health_check, name="health_check"),  # Health check endpoint
]
urlpatterns += router.urls
