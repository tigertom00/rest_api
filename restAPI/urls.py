from django.urls import path, re_path
from rest_framework import routers
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


router = routers.DefaultRouter()
router.register('user', views.UsersViewSet, 'users')


urlpatterns = [
    #path('', views.index, name='index'),
    path("", views.landing_page, name="landing"),
    path('register/' , views.CreateUsersViewSet.as_view(), name='register'),
    #path('dj-rest-auth/', include('dj_rest_auth.urls')),
    #path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', views.BlacklistTokenView.as_view(), name='blacklist_token'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('clerk/webhook/', views.clerk_webhook, name='clerk_webhook'),
    #path('nextcloud/files/', views.fetch_nextcloud_files, name='fetch_nextcloud_files'),
    #path('nextcloud/upload/', views.upload_file, name='upload_filev'),
    #path('nextcloud/contacts/', views.fetch_contacts, name='fetch_contacts'),
    #path('nextcloud/calendar/', views.calendar, name='calendar'),
]
urlpatterns += router.urls