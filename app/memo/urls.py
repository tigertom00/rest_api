from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActiveTimerSessionViewSet,
    DashboardViewSet,
    ElektriskKategoriViewSet,
    JobberFileViewSet,
    JobberImageViewSet,
    JobberTaskViewSet,
    JobberViewSet,
    JobbMatriellViewSet,
    LeverandorerViewSet,
    MatriellViewSet,
    TimelisteViewSet,
)

router = DefaultRouter()
router.register(r"dashboard", DashboardViewSet, basename="dashboard")
router.register(r"elektrisk-kategorier", ElektriskKategoriViewSet)
router.register(r"leverandorer", LeverandorerViewSet)
router.register(r"matriell", MatriellViewSet)
router.register(r"jobber", JobberViewSet)
router.register(r"jobbmatriell", JobbMatriellViewSet)
router.register(r"jobb-images", JobberImageViewSet)
router.register(r"jobb-files", JobberFileViewSet)
router.register(r"jobber-tasks", JobberTaskViewSet)
router.register(r"timeliste", TimelisteViewSet)
router.register(r"timer", ActiveTimerSessionViewSet, basename="timer")


urlpatterns = [
    path("", include(router.urls)),
]
