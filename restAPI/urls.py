from django.urls import path, include
from rest_framework import routers
from .views import index, UsersViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)



router = routers.DefaultRouter()
router.register('user/', UsersViewSet, 'users')


urlpatterns = [
    path('', index, name='index'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
]
urlpatterns += router.urls