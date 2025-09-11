from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, JobberImage, JobberFile, Timeliste
from .serializers import (
    LeverandorerSerializer,
    MatriellSerializer,
    JobberSerializer,
    JobbMatriellSerializer,
    JobberImageSerializer,
    JobberFileSerializer,
    TimelisteSerializer,
)


class LeverandorerViewSet(viewsets.ModelViewSet):
    queryset = Leverandorer.objects.all().order_by("-created_at")
    serializer_class = LeverandorerSerializer
    permission_classes = [IsAuthenticated]


class MatriellViewSet(viewsets.ModelViewSet):
    queryset = Matriell.objects.all().order_by("-created_at")
    serializer_class = MatriellSerializer
    permission_classes = [IsAuthenticated]


class JobberViewSet(viewsets.ModelViewSet):
    queryset = Jobber.objects.all().order_by("-created_at")
    serializer_class = JobberSerializer
    permission_classes = [IsAuthenticated]


class JobbMatriellViewSet(viewsets.ModelViewSet):
    queryset = JobbMatriell.objects.all().order_by("-created_at")
    serializer_class = JobbMatriellSerializer
    permission_classes = [IsAuthenticated]

class JobberImageViewSet(viewsets.ModelViewSet):
    queryset = JobberImage.objects.all().order_by("-created_at")
    serializer_class = JobberImageSerializer
    permission_classes = [IsAuthenticated]


class JobberFileViewSet(viewsets.ModelViewSet):
    queryset = JobberFile.objects.all().order_by("-created_at")
    serializer_class = JobberFileSerializer
    permission_classes = [IsAuthenticated]


class TimelisteViewSet(viewsets.ModelViewSet):
    queryset = Timeliste.objects.all().order_by("-created_at")
    serializer_class = TimelisteSerializer
    permission_classes = [IsAuthenticated]
