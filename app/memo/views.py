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
    MatriellFavoriteSerializer,
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

    @action(detail=True, methods=["post", "delete", "get"])
    def favorite(self, request, pk=None):
        """
        Manage favorites for a Matriell item.
        - POST: Add to favorites
        - DELETE: Remove from favorites
        - GET: Check favorite status
        """
        matriell = self.get_object()

        if request.method == "POST":
            if matriell.favorites:
                return Response(
                    {"message": "Item is already in favorites", "favorites": True},
                    status=status.HTTP_200_OK
                )

            matriell.favorites = True
            matriell.save()

            return Response(
                {"message": "Item added to favorites", "favorites": True},
                status=status.HTTP_201_CREATED
            )

        elif request.method == "DELETE":
            if not matriell.favorites:
                return Response(
                    {"message": "Item is not in favorites", "favorites": False},
                    status=status.HTTP_200_OK
                )

            matriell.favorites = False
            matriell.save()

            return Response(
                {"message": "Item removed from favorites", "favorites": False},
                status=status.HTTP_204_NO_CONTENT
            )

        elif request.method == "GET":
            return Response(
                {
                    "el_nr": matriell.el_nr,
                    "tittel": matriell.tittel,
                    "favorites": matriell.favorites
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=["get"])
    def favorites(self, request):
        """
        List all favorite Matriell items with pagination.
        Uses optimized serializer for better performance.
        """
        favorites_queryset = self.get_queryset().filter(favorites=True).select_related('leverandor', 'kategori')
        page = self.paginate_queryset(favorites_queryset)

        if page is not None:
            serializer = MatriellFavoriteSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MatriellFavoriteSerializer(favorites_queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_favorite(self, request):
        """
        Bulk favorite/unfavorite operations.
        Expects: {"action": "add|remove", "el_nrs": ["2050783", "2050782"]}
        """
        action_type = request.data.get("action")
        el_nrs = request.data.get("el_nrs", [])

        if action_type not in ["add", "remove"]:
            return Response(
                {"error": "Action must be 'add' or 'remove'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not el_nrs:
            return Response(
                {"error": "el_nrs list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorites_value = action_type == "add"
        updated_count = Matriell.objects.filter(
            el_nr__in=el_nrs
        ).update(favorites=favorites_value)

        action_text = "added to" if action_type == "add" else "removed from"
        return Response(
            {
                "message": f"{updated_count} items {action_text} favorites",
                "updated_count": updated_count,
                "action": action_type
            },
            status=status.HTTP_200_OK
        )


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
