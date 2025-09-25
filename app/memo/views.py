from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ElektriskKategori,
    Jobber,
    JobberFile,
    JobberImage,
    JobbMatriell,
    Leverandorer,
    Matriell,
    Timeliste,
)
from .serializers import (
    EFOBasenImportSerializer,
    ElektriskKategoriSerializer,
    JobberFileSerializer,
    JobberImageSerializer,
    JobberSerializer,
    JobbMatriellSerializer,
    LeverandorerCreateSerializer,
    LeverandorerSerializer,
    MatriellSerializer,
    TimelisteSerializer,
)


class ElektriskKategoriViewSet(viewsets.ModelViewSet):
    queryset = ElektriskKategori.objects.all().order_by("blokknummer")
    serializer_class = ElektriskKategoriSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


class LeverandorerViewSet(viewsets.ModelViewSet):
    queryset = Leverandorer.objects.all().order_by("-created_at")
    serializer_class = LeverandorerSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return LeverandorerCreateSerializer
        return super().get_serializer_class()


class MatriellViewSet(viewsets.ModelViewSet):
    queryset = Matriell.objects.all().order_by("-created_at")
    serializer_class = MatriellSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "efobasen_import":
            return EFOBasenImportSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["post"])
    def efobasen_import(self, request):
        """
        Import data from EFO Basen JSON format.
        Expects the structured JSON format with foreign key lookups by name/blokknummer.
        Accepts both single objects and arrays of objects.
        """
        data = request.data
        if not isinstance(data, list):
            data = [data]

        results = {
            "created": 0,
            "updated": 0,
            "errors": [],
            "total_processed": len(data),
        }

        with transaction.atomic():
            for i, item in enumerate(data):
                try:
                    el_nr = item.get("el_nr")
                    if not el_nr:
                        results["errors"].append(f"Item {i}: Missing el_nr")
                        continue

                    # Check if product already exists
                    existing = Matriell.objects.filter(el_nr=el_nr).first()
                    if existing:
                        # Update existing
                        serializer = self.get_serializer(
                            existing, data=item, partial=True
                        )
                        if serializer.is_valid():
                            serializer.save()
                            results["updated"] += 1
                        else:
                            results["errors"].append(
                                f"Item {i} (el_nr: {el_nr}): {serializer.errors}"
                            )
                    else:
                        # Create new
                        serializer = self.get_serializer(data=item)
                        if serializer.is_valid():
                            serializer.save()
                            results["created"] += 1
                        else:
                            results["errors"].append(
                                f"Item {i} (el_nr: {el_nr}): {serializer.errors}"
                            )

                except Exception as e:
                    results["errors"].append(f"Item {i}: {str(e)}")

        # Determine response status
        if results["errors"]:
            response_status = status.HTTP_207_MULTI_STATUS  # Partial success
        else:
            response_status = status.HTTP_201_CREATED

        return Response(results, status=response_status)


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
