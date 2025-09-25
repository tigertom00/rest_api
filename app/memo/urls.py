from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ElektriskKategoriViewSet,
    JobberFileViewSet,
    JobberImageViewSet,
    JobberViewSet,
    JobbMatriellViewSet,
    LeverandorerViewSet,
    MatriellViewSet,
    TimelisteViewSet,
)

router = DefaultRouter()
router.register(r"elektrisk-kategorier", ElektriskKategoriViewSet)
router.register(r"leverandorer", LeverandorerViewSet)
router.register(r"matriell", MatriellViewSet)
router.register(r"jobber", JobberViewSet)
router.register(r"jobbmatriell", JobbMatriellViewSet)
router.register(r"jobb-images", JobberImageViewSet)
router.register(r"jobb-files", JobberFileViewSet)
router.register(r"timeliste", TimelisteViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
