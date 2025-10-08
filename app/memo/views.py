from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .filters import (
    ElektriskKategoriFilter,
    JobberFilter,
    JobberTaskFilter,
    JobbMatriellFilter,
    LeverandorerFilter,
    TimelisteFilter,
)
from .models import (
    ActiveTimerSession,
    ElektriskKategori,
    Jobber,
    JobberFile,
    JobberImage,
    JobberTask,
    JobbMatriell,
    Leverandorer,
    Matriell,
    Timeliste,
)
from .serializers import (
    ActiveTimerSessionSerializer,
    EFOBasenImportSerializer,
    ElektriskKategoriSerializer,
    JobberFileSerializer,
    JobberImageSerializer,
    JobberSerializer,
    JobberTaskSerializer,
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ElektriskKategoriFilter
    search_fields = ["kategori", "beskrivelse", "blokknummer"]

    @action(detail=False, methods=["get"])
    def choices(self, request):
        """
        Get minimal data for dropdown/select components.
        Returns only id, kategori, and blokknummer for performance.
        """
        queryset = (
            self.get_queryset()
            .values("id", "kategori", "blokknummer")
            .order_by("blokknummer")
        )

        # Apply search if provided
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(kategori__icontains=search) | Q(blokknummer__icontains=search)
            )

        # Limit results for performance
        limit = min(int(request.query_params.get("limit", 100)), 500)
        queryset = queryset[:limit]

        return Response(list(queryset))


class LeverandorerViewSet(viewsets.ModelViewSet):
    queryset = Leverandorer.objects.all().order_by("-created_at")
    serializer_class = LeverandorerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = LeverandorerFilter
    search_fields = ["name", "addresse", "poststed", "epost"]

    def get_serializer_class(self):
        if self.action == "create":
            return LeverandorerCreateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        """
        Quick lookup for a single Leverandor by name.
        Usage: /leverandorer/lookup/?name=nexans
        """
        name = request.query_params.get("name")
        if not name:
            return Response(
                {"error": "name parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            leverandor = Leverandorer.objects.get(name__icontains=name)
            serializer = self.get_serializer(leverandor)
            return Response(serializer.data)
        except Leverandorer.DoesNotExist:
            return Response(
                {"error": f"Leverandor with name containing '{name}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Leverandorer.MultipleObjectsReturned:
            # Return first match if multiple found
            leverandor = Leverandorer.objects.filter(name__icontains=name).first()
            serializer = self.get_serializer(leverandor)
            return Response(
                {
                    "warning": f"Multiple suppliers found for '{name}', returning first match",
                    **serializer.data,
                }
            )

    @action(detail=False, methods=["get"])
    def choices(self, request):
        """
        Get minimal data for dropdown/select components.
        Returns only id and name for performance.
        """
        queryset = self.get_queryset().values("id", "name").order_by("name")

        # Apply search if provided
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Limit results for performance
        limit = min(int(request.query_params.get("limit", 100)), 500)
        queryset = queryset[:limit]

        return Response(list(queryset))


class MatriellViewSet(viewsets.ModelViewSet):
    queryset = Matriell.objects.all().order_by("-created_at")
    serializer_class = MatriellSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "efobasen_import":
            return EFOBasenImportSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        """
        Quick lookup for a single Matriell item by el_nr.
        Usage: /matriell/lookup/?el_nr=1000001
        """
        el_nr = request.query_params.get("el_nr")
        if not el_nr:
            return Response(
                {"error": "el_nr parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            matriell = Matriell.objects.select_related("leverandor", "kategori").get(
                el_nr=el_nr
            )
            serializer = self.get_serializer(matriell)
            return Response(serializer.data)
        except Matriell.DoesNotExist:
            return Response(
                {"error": f"Matriell with el_nr '{el_nr}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def choices(self, request):
        """
        Get minimal data for dropdown/select components.
        Returns only id, el_nr, and tittel for performance.
        """
        queryset = self.get_queryset().values("id", "el_nr", "tittel").order_by("el_nr")

        # Apply basic filtering if provided
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(el_nr__icontains=search) | Q(tittel__icontains=search)
            )

        # Limit results for performance
        limit = min(int(request.query_params.get("limit", 100)), 500)
        queryset = queryset[:limit]

        return Response(list(queryset))

    @action(detail=False, methods=["get"])
    def duplicates(self, request):
        """
        Find potential duplicate Matriell items based on similar titles or product numbers.
        """
        # Find items with similar titles (using basic similarity)
        potential_duplicates = []

        # Group by similar varenummer (product numbers)
        items_with_varenummer = (
            Matriell.objects.exclude(varenummer__isnull=True)
            .exclude(varenummer__exact="")
            .values("varenummer")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for item in items_with_varenummer:
            duplicates = Matriell.objects.filter(
                varenummer=item["varenummer"]
            ).select_related("leverandor")

            potential_duplicates.append(
                {
                    "type": "varenummer",
                    "value": item["varenummer"],
                    "count": item["count"],
                    "items": [
                        {
                            "id": dup.id,
                            "el_nr": dup.el_nr,
                            "tittel": dup.tittel,
                            "leverandor_name": (
                                dup.leverandor.name if dup.leverandor else None
                            ),
                        }
                        for dup in duplicates
                    ],
                }
            )

        return Response(
            {
                "potential_duplicates": potential_duplicates,
                "total_groups": len(potential_duplicates),
            }
        )

    @action(detail=False, methods=["post"])
    def bulk_operations(self, request):
        """
        Perform bulk operations on Matriell items.
        Expects: {
            "action": "update_status|delete|approve|set_stock",
            "el_nrs": ["1000001", "1000002"],
            "data": {"approved": true, "in_stock": false} # for update operations
        }
        """
        action = request.data.get("action")
        el_nrs = request.data.get("el_nrs", [])
        data = request.data.get("data", {})

        if not action:
            return Response(
                {"error": "action is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not el_nrs:
            return Response(
                {"error": "el_nrs list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Matriell.objects.filter(el_nr__in=el_nrs)
        affected_count = queryset.count()

        if affected_count == 0:
            return Response(
                {"error": "No materials found with provided el_nrs"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if action == "update_status":
                # Bulk update status fields
                update_fields = {}
                if "approved" in data:
                    update_fields["approved"] = data["approved"]
                if "in_stock" in data:
                    update_fields["in_stock"] = data["in_stock"]
                if "discontinued" in data:
                    update_fields["discontinued"] = data["discontinued"]
                if "favorites" in data:
                    update_fields["favorites"] = data["favorites"]

                if not update_fields:
                    return Response(
                        {"error": "No valid update fields provided"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                queryset.update(**update_fields)
                return Response(
                    {
                        "message": f"Updated {affected_count} materials",
                        "affected_count": affected_count,
                        "action": action,
                        "updated_fields": list(update_fields.keys()),
                    }
                )

            elif action == "delete":
                # Bulk delete (soft delete by marking as discontinued)
                queryset.update(discontinued=True)
                return Response(
                    {
                        "message": f"Marked {affected_count} materials as discontinued",
                        "affected_count": affected_count,
                        "action": action,
                    }
                )

            elif action == "approve":
                # Bulk approve
                queryset.update(approved=True)
                return Response(
                    {
                        "message": f"Approved {affected_count} materials",
                        "affected_count": affected_count,
                        "action": action,
                    }
                )

            elif action == "set_stock":
                # Bulk stock update
                stock_status = data.get("in_stock", True)
                queryset.update(in_stock=stock_status)
                return Response(
                    {
                        "message": f"Set stock status to {stock_status} for {affected_count} materials",
                        "affected_count": affected_count,
                        "action": action,
                        "stock_status": stock_status,
                    }
                )

            else:
                return Response(
                    {
                        "error": f"Unknown action: {action}. Valid actions: update_status, delete, approve, set_stock"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"error": f"Bulk operation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def validate_material(self, request):
        """
        Validate material data before creation/update.
        Expects material data in the same format as create/update endpoints.
        """
        data = request.data

        # Use the serializer for validation without saving
        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            return Response(
                {
                    "valid": True,
                    "message": "Material data is valid",
                    "validated_data": serializer.validated_data,
                }
            )
        else:
            return Response(
                {
                    "valid": False,
                    "errors": serializer.errors,
                    "message": "Material data validation failed",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"])
    def efobasen_import(self, request):
        """
        Import data from EFO Basen JSON format.
        Expects the structured JSON format with foreign key lookups by name/blokknummer.
        Returns the created or updated Matriell object with full details.
        """
        data = request.data

        try:
            el_nr = data.get("el_nr")
            if not el_nr:
                return Response(
                    {"error": "Missing el_nr"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Check if product already exists
            existing = Matriell.objects.filter(el_nr=el_nr).first()
            if existing:
                # Update existing
                import_serializer = self.get_serializer(
                    existing, data=data, partial=True
                )
                if import_serializer.is_valid():
                    matriell = import_serializer.save()
                    # Return full object using MatriellSerializer
                    response_serializer = MatriellSerializer(matriell)
                    return Response(response_serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        import_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Create new
                import_serializer = self.get_serializer(data=data)
                if import_serializer.is_valid():
                    matriell = import_serializer.save()
                    # Return full object using MatriellSerializer
                    response_serializer = MatriellSerializer(matriell)
                    return Response(
                        response_serializer.data, status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        import_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
                    status=status.HTTP_200_OK,
                )

            matriell.favorites = True
            matriell.save()

            return Response(
                {"message": "Item added to favorites", "favorites": True},
                status=status.HTTP_201_CREATED,
            )

        elif request.method == "DELETE":
            if not matriell.favorites:
                return Response(
                    {"message": "Item is not in favorites", "favorites": False},
                    status=status.HTTP_200_OK,
                )

            matriell.favorites = False
            matriell.save()

            return Response(
                {"message": "Item removed from favorites", "favorites": False},
                status=status.HTTP_204_NO_CONTENT,
            )

        elif request.method == "GET":
            return Response(
                {
                    "el_nr": matriell.el_nr,
                    "tittel": matriell.tittel,
                    "favorites": matriell.favorites,
                },
                status=status.HTTP_200_OK,
            )

    @action(detail=False, methods=["get"])
    def favorites(self, request):
        """
        List all favorite Matriell items with pagination.
        Uses optimized serializer for better performance.
        """
        favorites_queryset = (
            self.get_queryset()
            .filter(favorites=True)
            .select_related("leverandor", "kategori")
        )
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not el_nrs:
            return Response(
                {"error": "el_nrs list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorites_value = action_type == "add"
        updated_count = Matriell.objects.filter(el_nr__in=el_nrs).update(
            favorites=favorites_value
        )

        action_text = "added to" if action_type == "add" else "removed from"
        return Response(
            {
                "message": f"{updated_count} items {action_text} favorites",
                "updated_count": updated_count,
                "action": action_type,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def validate_data(self, request):
        """
        Validate material data before creation/update.
        Checks for duplicates, required fields, and data integrity.
        """
        data = request.data
        errors = []
        warnings = []

        # Check required fields
        required_fields = ["el_nr", "tittel"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Field '{field}' is required")

        # Check for duplicate el_nr
        el_nr = data.get("el_nr")
        if el_nr:
            existing = Matriell.objects.filter(el_nr=el_nr).first()
            if existing:
                errors.append(
                    f"Material with el_nr '{el_nr}' already exists (ID: {existing.id})"
                )

        # Check for duplicate GTIN if provided
        gtin = data.get("gtin_number")
        if gtin:
            existing_gtin = Matriell.objects.filter(gtin_number=gtin).first()
            if existing_gtin:
                warnings.append(
                    f"GTIN '{gtin}' already exists for material '{existing_gtin.el_nr}'"
                )

        # Validate leverandor (supplier)
        leverandor_data = data.get("leverandor")
        if isinstance(leverandor_data, str):
            try:
                Leverandorer.objects.get(name=leverandor_data)
            except Leverandorer.DoesNotExist:
                errors.append(f"Leverandor '{leverandor_data}' not found")
        elif isinstance(leverandor_data, dict):
            # Validate supplier data structure
            supplier_name = leverandor_data.get("navn") or leverandor_data.get("name")
            if not supplier_name:
                errors.append("Supplier name is required in leverandor data")

        # Validate kategori (category)
        kategori_data = data.get("kategori")
        if kategori_data:
            try:
                ElektriskKategori.objects.get(blokknummer=kategori_data)
            except ElektriskKategori.DoesNotExist:
                errors.append(f"Category with blokknummer '{kategori_data}' not found")

        # Validate numeric fields
        numeric_fields = ["hoyde", "bredde", "lengde", "vekt"]
        for field in numeric_fields:
            value = data.get(field)
            if value is not None:
                try:
                    float_value = float(value)
                    if float_value < 0:
                        warnings.append(
                            f"Field '{field}' has negative value: {float_value}"
                        )
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be a valid number")

        # Validate URLs
        url_fields = ["produktblad", "produkt_url"]
        for field in url_fields:
            url = data.get(field)
            if url and not (url.startswith("http://") or url.startswith("https://")):
                warnings.append(
                    f"Field '{field}' should start with http:// or https://"
                )

        # Determine validation status
        is_valid = len(errors) == 0
        status_code = status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST

        return Response(
            {
                "valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "data_summary": {
                    "el_nr": el_nr,
                    "tittel": data.get("tittel"),
                    "leverandor": (
                        leverandor_data
                        if isinstance(leverandor_data, str)
                        else (
                            leverandor_data.get("navn") or leverandor_data.get("name")
                            if isinstance(leverandor_data, dict)
                            else None
                        )
                    ),
                    "kategori": kategori_data,
                    "has_gtin": bool(gtin),
                },
            },
            status=status_code,
        )

    @action(detail=False, methods=["get"])
    def check_duplicates(self, request):
        """
        Check for potential duplicate materials based on various criteria.
        Query params:
        - el_nr: Check specific el_nr
        - gtin_number: Check specific GTIN
        - tittel: Check similar titles
        - limit: Maximum results (default: 10)
        """
        el_nr = request.query_params.get("el_nr")
        gtin_number = request.query_params.get("gtin_number")
        tittel = request.query_params.get("tittel")
        limit = int(request.query_params.get("limit", 10))

        results = {}

        # Check el_nr duplicates
        if el_nr:
            duplicate_el_nr = Matriell.objects.filter(el_nr=el_nr).first()
            results["el_nr_duplicate"] = {
                "found": bool(duplicate_el_nr),
                "material": (
                    MatriellSerializer(duplicate_el_nr).data
                    if duplicate_el_nr
                    else None
                ),
            }

        # Check GTIN duplicates
        if gtin_number:
            duplicate_gtin = Matriell.objects.filter(gtin_number=gtin_number).first()
            results["gtin_duplicate"] = {
                "found": bool(duplicate_gtin),
                "material": (
                    MatriellSerializer(duplicate_gtin).data if duplicate_gtin else None
                ),
            }

        # Check similar titles
        if tittel:
            similar_titles = Matriell.objects.filter(tittel__icontains=tittel).exclude(
                tittel__iexact=tittel  # Exclude exact matches for similarity check
            )[:limit]

            results["similar_titles"] = {
                "count": similar_titles.count(),
                "materials": MatriellSerializer(similar_titles, many=True).data,
            }

        # Find potential duplicates based on combination of fields
        if not any([el_nr, gtin_number, tittel]):
            # General duplicate detection - find materials with same title + varemerke
            potential_duplicates = (
                Matriell.objects.values("tittel", "varemerke")
                .annotate(count=Count("id"))
                .filter(count__gt=1)
                .order_by("-count")[:limit]
            )

            duplicate_groups = []
            for dup in potential_duplicates:
                materials = Matriell.objects.filter(
                    tittel=dup["tittel"], varemerke=dup["varemerke"]
                )
                duplicate_groups.append(
                    {
                        "criteria": {
                            "tittel": dup["tittel"],
                            "varemerke": dup["varemerke"],
                        },
                        "count": dup["count"],
                        "materials": MatriellSerializer(materials, many=True).data,
                    }
                )

            results["potential_duplicates"] = {
                "groups": duplicate_groups,
                "total_groups": len(duplicate_groups),
            }

        return Response(
            {
                "query": {
                    "el_nr": el_nr,
                    "gtin_number": gtin_number,
                    "tittel": tittel,
                    "limit": limit,
                },
                "results": results,
            }
        )

    @action(detail=False, methods=["post"])
    def merge_duplicates(self, request):
        """
        Merge duplicate materials by keeping the primary and updating references.
        Expected data: {
            "primary_id": int,
            "duplicate_ids": [int, int, ...],
            "update_references": boolean (default: true)
        }
        """
        primary_id = request.data.get("primary_id")
        duplicate_ids = request.data.get("duplicate_ids", [])
        update_references = request.data.get("update_references", True)

        if not primary_id:
            return Response(
                {"error": "primary_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not duplicate_ids:
            return Response(
                {"error": "duplicate_ids list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            primary_material = Matriell.objects.get(id=primary_id)
        except Matriell.DoesNotExist:
            return Response(
                {"error": f"Primary material with ID {primary_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate all duplicate materials exist
        duplicate_materials = Matriell.objects.filter(id__in=duplicate_ids)
        if len(duplicate_materials) != len(duplicate_ids):
            found_ids = list(duplicate_materials.values_list("id", flat=True))
            missing_ids = [id for id in duplicate_ids if id not in found_ids]
            return Response(
                {"error": f"Materials not found: {missing_ids}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        merge_summary = {
            "primary_material": {
                "id": primary_material.id,
                "el_nr": primary_material.el_nr,
                "tittel": primary_material.tittel,
            },
            "duplicates_removed": [],
            "references_updated": 0,
        }

        # Update references if requested
        if update_references:
            for duplicate in duplicate_materials:
                # Update JobbMatriell references
                updated_refs = JobbMatriell.objects.filter(matriell=duplicate).update(
                    matriell=primary_material
                )
                merge_summary["references_updated"] += updated_refs

                merge_summary["duplicates_removed"].append(
                    {
                        "id": duplicate.id,
                        "el_nr": duplicate.el_nr,
                        "tittel": duplicate.tittel,
                        "references_moved": updated_refs,
                    }
                )

        # Delete duplicate materials
        duplicate_materials.delete()

        return Response(
            {
                "message": f"Successfully merged {len(duplicate_ids)} duplicate materials",
                "merge_summary": merge_summary,
            },
            status=status.HTTP_200_OK,
        )


class DashboardViewSet(ViewSet):
    """
    Dashboard endpoints providing statistics and overview data for the memo app.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get overall statistics for the memo app.
        """
        # Material statistics
        total_materials = Matriell.objects.count()
        favorite_materials = Matriell.objects.filter(favorites=True).count()
        approved_materials = Matriell.objects.filter(approved=True).count()
        in_stock_materials = Matriell.objects.filter(in_stock=True).count()
        discontinued_materials = Matriell.objects.filter(discontinued=True).count()

        # Job statistics
        total_jobs = Jobber.objects.count()
        completed_jobs = Jobber.objects.filter(ferdig=True).count()
        active_jobs = Jobber.objects.filter(ferdig=False).count()

        # Calculate total hours across all jobs
        total_hours = sum(job.total_hours for job in Jobber.objects.all())

        # Supplier statistics
        total_suppliers = Leverandorer.objects.count()
        suppliers_with_materials = (
            Leverandorer.objects.annotate(material_count=Count("matriell"))
            .filter(material_count__gt=0)
            .count()
        )

        # Category statistics
        total_categories = ElektriskKategori.objects.count()
        categories_with_materials = (
            ElektriskKategori.objects.annotate(material_count=Count("matriell"))
            .filter(material_count__gt=0)
            .count()
        )

        # Time tracking statistics
        total_time_entries = Timeliste.objects.count()
        time_entries_this_month = Timeliste.objects.filter(
            created_at__month=timezone.now().month, created_at__year=timezone.now().year
        ).count()

        return Response(
            {
                "materials": {
                    "total": total_materials,
                    "favorites": favorite_materials,
                    "approved": approved_materials,
                    "in_stock": in_stock_materials,
                    "discontinued": discontinued_materials,
                    "approval_rate": round(
                        (
                            (approved_materials / total_materials * 100)
                            if total_materials > 0
                            else 0
                        ),
                        1,
                    ),
                },
                "jobs": {
                    "total": total_jobs,
                    "completed": completed_jobs,
                    "active": active_jobs,
                    "completion_rate": round(
                        (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0, 1
                    ),
                    "total_hours": total_hours,
                },
                "suppliers": {
                    "total": total_suppliers,
                    "with_materials": suppliers_with_materials,
                    "utilization_rate": round(
                        (
                            (suppliers_with_materials / total_suppliers * 100)
                            if total_suppliers > 0
                            else 0
                        ),
                        1,
                    ),
                },
                "categories": {
                    "total": total_categories,
                    "with_materials": categories_with_materials,
                    "utilization_rate": round(
                        (
                            (categories_with_materials / total_categories * 100)
                            if total_categories > 0
                            else 0
                        ),
                        1,
                    ),
                },
                "time_tracking": {
                    "total_entries": total_time_entries,
                    "entries_this_month": time_entries_this_month,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        Get recent activities across all models.
        """
        # Recent materials (last 10)
        recent_materials = Matriell.objects.select_related(
            "leverandor", "kategori"
        ).order_by("-created_at")[:10]

        # Recent jobs (last 10)
        recent_jobs = Jobber.objects.order_by("-created_at")[:10]

        # Recent time entries (last 10)
        recent_time_entries = Timeliste.objects.select_related("user", "jobb").order_by(
            "-created_at"
        )[:10]

        # Serialize the data
        from .serializers import (
            MatriellFavoriteSerializer,
        )

        return Response(
            {
                "materials": MatriellFavoriteSerializer(
                    recent_materials, many=True
                ).data,
                "jobs": [
                    {
                        "id": job.ordre_nr,
                        "tittel": job.tittel,
                        "ferdig": job.ferdig,
                        "created_at": job.created_at,
                    }
                    for job in recent_jobs
                ],
                "time_entries": [
                    {
                        "id": entry.id,
                        "beskrivelse": entry.beskrivelse,
                        "timer": entry.timer,
                        "dato": entry.dato,
                        "jobb_tittel": entry.jobb.tittel if entry.jobb else None,
                        "user": entry.user.username if entry.user else None,
                        "created_at": entry.created_at,
                    }
                    for entry in recent_time_entries
                ],
            }
        )

    @action(detail=False, methods=["get"])
    def quick_access(self, request):
        """
        Get frequently used items and shortcuts for quick access.
        """
        # Most used materials (by job usage)
        popular_materials = (
            Matriell.objects.annotate(usage_count=Count("jobbmatriell"))
            .filter(usage_count__gt=0)
            .order_by("-usage_count")[:10]
        )

        # Favorite materials
        favorite_materials = Matriell.objects.filter(favorites=True).order_by(
            "-updated_at"
        )[:5]

        # Active jobs
        active_jobs = Jobber.objects.filter(ferdig=False).order_by("-created_at")[:5]

        # Most used suppliers
        popular_suppliers = (
            Leverandorer.objects.annotate(material_count=Count("matriell"))
            .filter(material_count__gt=0)
            .order_by("-material_count")[:5]
        )

        return Response(
            {
                "popular_materials": [
                    {
                        "id": material.id,
                        "el_nr": material.el_nr,
                        "tittel": material.tittel,
                        "usage_count": material.usage_count,
                        "leverandor_name": (
                            material.leverandor.name if material.leverandor else None
                        ),
                    }
                    for material in popular_materials
                ],
                "favorite_materials": MatriellFavoriteSerializer(
                    favorite_materials, many=True
                ).data,
                "active_jobs": [
                    {
                        "id": job.ordre_nr,
                        "tittel": job.tittel,
                        "created_at": job.created_at,
                        "material_count": job.jobbmatriell.count(),
                    }
                    for job in active_jobs
                ],
                "popular_suppliers": [
                    {
                        "id": supplier.id,
                        "name": supplier.name,
                        "material_count": supplier.material_count,
                    }
                    for supplier in popular_suppliers
                ],
            }
        )


class JobberViewSet(viewsets.ModelViewSet):
    queryset = Jobber.objects.all().order_by("-created_at")
    serializer_class = JobberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = JobberFilter
    search_fields = ["tittel", "adresse", "beskrivelse"]

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        """
        Quick lookup for a single Jobb by ordre_nr.
        Usage: /jobber/lookup/?ordre_nr=123
        """
        ordre_nr = request.query_params.get("ordre_nr")
        if not ordre_nr:
            return Response(
                {"error": "ordre_nr parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jobb = Jobber.objects.prefetch_related("jobbmatriell__matriell").get(
                ordre_nr=ordre_nr
            )
            serializer = self.get_serializer(jobb)
            return Response(serializer.data)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Jobb with ordre_nr '{ordre_nr}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"])
    def add_materials(self, request, pk=None):
        """
        Add multiple materials to a job.
        Expects: {"materials": [{"matriell_id": 1, "antall": 5, "transf": false}, ...]}
        """
        jobb = self.get_object()
        materials_data = request.data.get("materials", [])

        if not materials_data:
            return Response(
                {"error": "materials list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_materials = []
        errors = []

        for material_data in materials_data:
            try:
                matriell_id = material_data.get("matriell_id")
                antall = material_data.get("antall", 1)
                transf = material_data.get("transf", False)

                if not matriell_id:
                    errors.append("matriell_id is required for each material")
                    continue

                # Check if material exists
                try:
                    matriell = Matriell.objects.get(id=matriell_id)
                except Matriell.DoesNotExist:
                    errors.append(f"Matriell with id {matriell_id} not found")
                    continue

                # Create or update JobbMatriell
                jobb_matriell, created = JobbMatriell.objects.get_or_create(
                    jobb=jobb,
                    matriell=matriell,
                    defaults={"antall": antall, "transf": transf, "user": request.user},
                )

                if not created:
                    # Update existing
                    jobb_matriell.antall += antall
                    jobb_matriell.transf = transf
                    jobb_matriell.save()

                created_materials.append(
                    {
                        "matriell_id": matriell.id,
                        "el_nr": matriell.el_nr,
                        "tittel": matriell.tittel,
                        "antall": jobb_matriell.antall,
                        "transf": jobb_matriell.transf,
                        "action": "created" if created else "updated",
                    }
                )

            except Exception as e:
                errors.append(f"Error processing material {material_data}: {str(e)}")

        return Response(
            {
                "message": f"Processed {len(created_materials)} materials for job {jobb.ordre_nr}",
                "materials": created_materials,
                "errors": errors,
                "total_materials_in_job": jobb.jobbmatriell.count(),
            }
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Mark job as complete with optional completion notes.
        Expects: {"notes": "Job completed successfully"}
        """
        jobb = self.get_object()

        if jobb.ferdig:
            return Response(
                {"message": "Job is already marked as complete", "ferdig": True},
                status=status.HTTP_200_OK,
            )

        # Optional completion validation
        materials_count = jobb.jobbmatriell.count()
        if materials_count == 0:
            return Response(
                {"error": "Cannot complete job without any materials assigned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jobb.ferdig = True

        # Add completion notes to description if provided
        notes = request.data.get("notes")
        if notes:
            if jobb.beskrivelse:
                jobb.beskrivelse += f"\n\nCompletion notes: {notes}"
            else:
                jobb.beskrivelse = f"Completion notes: {notes}"

        jobb.save()

        return Response(
            {
                "message": "Job marked as complete",
                "ordre_nr": jobb.ordre_nr,
                "tittel": jobb.tittel,
                "ferdig": jobb.ferdig,
                "total_hours": jobb.total_hours,
                "total_materials": materials_count,
                "completion_date": jobb.updated_at,
            }
        )

    @action(detail=True, methods=["get"])
    def materials_summary(self, request, pk=None):
        """
        Get detailed materials summary for a job.
        """
        jobb = self.get_object()

        materials = (
            JobbMatriell.objects.filter(jobb=jobb)
            .select_related("matriell__leverandor", "matriell__kategori")
            .order_by("matriell__el_nr")
        )

        materials_data = []
        total_items = 0

        for jobb_material in materials:
            material = jobb_material.matriell
            total_items += jobb_material.antall

            materials_data.append(
                {
                    "id": jobb_material.id,
                    "matriell_id": material.id,
                    "el_nr": material.el_nr,
                    "tittel": material.tittel,
                    "varemerke": material.varemerke,
                    "leverandor_name": (
                        material.leverandor.name if material.leverandor else None
                    ),
                    "kategori_name": (
                        material.kategori.kategori if material.kategori else None
                    ),
                    "antall": jobb_material.antall,
                    "transf": jobb_material.transf,
                    "in_stock": material.in_stock,
                    "approved": material.approved,
                }
            )

        # Group by category for summary
        category_summary = {}
        for item in materials_data:
            cat = item["kategori_name"] or "Ukategorisert"
            if cat not in category_summary:
                category_summary[cat] = {"count": 0, "items": 0}
            category_summary[cat]["count"] += 1
            category_summary[cat]["items"] += item["antall"]

        return Response(
            {
                "jobb": {
                    "ordre_nr": jobb.ordre_nr,
                    "tittel": jobb.tittel,
                    "ferdig": jobb.ferdig,
                },
                "summary": {
                    "total_material_types": len(materials_data),
                    "total_items": total_items,
                    "categories": len(category_summary),
                },
                "category_breakdown": category_summary,
                "materials": materials_data,
            }
        )

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """
        Get jobs near a location based on GPS coordinates.

        Query parameters:
            - lat (required): User's latitude
            - lon (required): User's longitude
            - radius (optional, default=100): Search radius in meters
            - ferdig (optional): Filter by completion status (true/false)

        Returns:
            List of jobs within radius, sorted by distance
        """
        from restAPI.services import GeocodingService

        # Validate required parameters
        try:
            user_lat = float(request.query_params.get("lat"))
            user_lon = float(request.query_params.get("lon"))
        except (TypeError, ValueError):
            return Response(
                {"error": "lat and lon are required and must be valid numbers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional parameters
        radius = float(request.query_params.get("radius", 100))
        ferdig = request.query_params.get("ferdig")

        # Start with jobs that have coordinates
        queryset = self.queryset.filter(latitude__isnull=False, longitude__isnull=False)

        # Filter by completion status if provided
        if ferdig is not None:
            queryset = queryset.filter(ferdig=ferdig.lower() == "true")

        # Performance optimization: bounding box pre-filter
        bbox = GeocodingService.get_bounding_box(user_lat, user_lon, radius)
        queryset = queryset.filter(
            latitude__gte=bbox["lat_min"],
            latitude__lte=bbox["lat_max"],
            longitude__gte=bbox["lon_min"],
            longitude__lte=bbox["lon_max"],
        )

        # Calculate exact distances and filter by radius
        nearby_jobs = []
        for job in queryset:
            distance = GeocodingService.calculate_distance(
                user_lat, user_lon, float(job.latitude), float(job.longitude)
            )

            if distance <= radius:
                nearby_jobs.append({"job": job, "distance": distance})

        # Sort by distance (closest first)
        nearby_jobs.sort(key=lambda x: x["distance"])

        # Paginate results
        jobs_list = [item["job"] for item in nearby_jobs]
        page = self.paginate_queryset(jobs_list)

        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"user_lat": user_lat, "user_lon": user_lon}
            )
            return self.get_paginated_response(serializer.data)

        # Serialize with distance context
        serializer = self.get_serializer(
            jobs_list, many=True, context={"user_lat": user_lat, "user_lon": user_lon}
        )

        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def heatmap(self, request):
        """
        Get job locations for heatmap visualization.

        Query parameters:
            - ferdig (optional): Filter by completion status (true/false)

        Returns:
            List of job coordinates with minimal data for map visualization
        """
        queryset = self.queryset.filter(latitude__isnull=False, longitude__isnull=False)

        # Optional filter by completion status
        ferdig = request.query_params.get("ferdig")
        if ferdig is not None:
            queryset = queryset.filter(ferdig=ferdig.lower() == "true")

        # Return lightweight data for visualization
        heatmap_data = [
            {
                "lat": float(job.latitude),
                "lon": float(job.longitude),
                "ordre_nr": job.ordre_nr,
                "tittel": job.tittel,
                "ferdig": job.ferdig,
            }
            for job in queryset
        ]

        return Response(
            {
                "total_jobs": len(heatmap_data),
                "jobs": heatmap_data,
            }
        )


class JobbMatriellViewSet(viewsets.ModelViewSet):
    queryset = JobbMatriell.objects.all().order_by("-created_at")
    serializer_class = JobbMatriellSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = JobbMatriellFilter
    search_fields = ["matriell__el_nr", "matriell__tittel", "jobb__tittel"]

    def perform_create(self, serializer):
        """Automatically set the user from the request when creating JobbMatriell."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        Get materials added to jobs in the last N days.
        Query params:
        - days: Number of days to look back (default: 30)
        - jobb_id: Filter by specific job (optional)
        - user_id: Filter by specific user (optional, defaults to current user)
        - all_users: Set to 'true' to see all users' additions (default: false)
        """
        from datetime import timedelta

        # Get days parameter (default to 30)
        try:
            days = int(request.query_params.get("days", 30))
            if days < 1:
                return Response(
                    {"error": "days parameter must be at least 1"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "days parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        # Start with base queryset
        queryset = JobbMatriell.objects.filter(
            created_at__gte=cutoff_date
        ).select_related("matriell__leverandor", "matriell__kategori", "jobb", "user")

        # User filtering
        all_users = request.query_params.get("all_users", "").lower() == "true"
        user_id = request.query_params.get("user_id")

        if not all_users:
            if user_id:
                # Filter by specific user
                from django.contrib.auth import get_user_model

                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    queryset = queryset.filter(user=user)
                except User.DoesNotExist:
                    return Response(
                        {"error": f"User with id {user_id} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                # Default to current user
                queryset = queryset.filter(user=request.user)

        # Optional job filter
        jobb_id = request.query_params.get("jobb_id")
        if jobb_id:
            try:
                jobb = Jobber.objects.get(ordre_nr=jobb_id)
                queryset = queryset.filter(jobb=jobb)
            except Jobber.DoesNotExist:
                return Response(
                    {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Order by most recent first
        queryset = queryset.order_by("-created_at")

        # Serialize the results using the serializer for consistent formatting
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "days": days,
                "cutoff_date": cutoff_date,
                "jobb_id": jobb_id,
                "user_id": user_id,
                "all_users": all_users,
                "total_count": queryset.count(),
                "results": serializer.data,
            }
        )


class JobberImageViewSet(viewsets.ModelViewSet):
    queryset = JobberImage.objects.all().order_by("-created_at")
    serializer_class = JobberImageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name", "jobb__tittel", "jobb__ordre_nr"]

    def get_queryset(self):
        """Optimize queryset with select_related"""
        return JobberImage.objects.select_related("jobb").order_by("-created_at")

    @action(detail=False, methods=["get"])
    def by_job(self, request):
        """
        Get all images for a specific job.
        Query params: jobb_id (ordre_nr)
        """
        jobb_id = request.query_params.get("jobb_id")
        if not jobb_id:
            return Response(
                {"error": "jobb_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        images = JobberImage.objects.filter(jobb=jobb).order_by("-created_at")
        serializer = self.get_serializer(images, many=True)

        return Response(
            {
                "jobb": {"ordre_nr": jobb.ordre_nr, "tittel": jobb.tittel},
                "image_count": images.count(),
                "images": serializer.data,
            }
        )

    @action(detail=False, methods=["post"])
    def bulk_upload(self, request):
        """
        Upload multiple images for a job at once.
        Expected format: {'jobb_id': 'xxx', 'images': [file1, file2, ...], 'names': ['name1', 'name2', ...]}
        """
        jobb_id = request.data.get("jobb_id")
        if not jobb_id:
            return Response(
                {"error": "jobb_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Handle multiple files
        files = request.FILES.getlist("images")
        names = request.data.getlist("names", [])

        if not files:
            return Response(
                {"error": "No images provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        created_images = []
        errors = []

        for i, file in enumerate(files):
            # Use provided name or default to filename
            name = names[i] if i < len(names) else file.name

            try:
                image = JobberImage.objects.create(jobb=jobb, image=file, name=name)
                created_images.append(
                    {"id": image.id, "name": image.name, "filename": file.name}
                )
            except Exception as e:
                errors.append({"filename": file.name, "error": str(e)})

        return Response(
            {
                "message": f"{len(created_images)} images uploaded successfully",
                "jobb_id": jobb_id,
                "uploaded": created_images,
                "errors": errors,
                "total_images": JobberImage.objects.filter(jobb=jobb).count(),
            },
            status=(
                status.HTTP_201_CREATED
                if created_images
                else status.HTTP_400_BAD_REQUEST
            ),
        )

    @action(detail=True, methods=["post"])
    def set_primary(self, request, pk=None):
        """
        Set an image as primary for the job (custom field can be added to model if needed).
        """
        image = self.get_object()

        # For now, just return success - can be enhanced when primary field is added to model
        return Response(
            {
                "message": f"Image '{image.name}' set as primary for job {image.jobb.ordre_nr}",
                "image_id": image.id,
                "jobb_id": image.jobb.ordre_nr,
            }
        )


class JobberFileViewSet(viewsets.ModelViewSet):
    queryset = JobberFile.objects.all().order_by("-created_at")
    serializer_class = JobberFileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name", "jobb__tittel", "jobb__ordre_nr"]

    def get_queryset(self):
        """Optimize queryset with select_related"""
        return JobberFile.objects.select_related("jobb").order_by("-created_at")

    @action(detail=False, methods=["get"])
    def by_job(self, request):
        """
        Get all files for a specific job.
        Query params: jobb_id (ordre_nr)
        """
        jobb_id = request.query_params.get("jobb_id")
        if not jobb_id:
            return Response(
                {"error": "jobb_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        files = JobberFile.objects.filter(jobb=jobb).order_by("-created_at")
        serializer = self.get_serializer(files, many=True)

        return Response(
            {
                "jobb": {"ordre_nr": jobb.ordre_nr, "tittel": jobb.tittel},
                "file_count": files.count(),
                "files": serializer.data,
            }
        )

    @action(detail=False, methods=["post"])
    def bulk_upload(self, request):
        """
        Upload multiple files for a job at once.
        Expected format: {'jobb_id': 'xxx', 'files': [file1, file2, ...], 'names': ['name1', 'name2', ...]}
        """
        jobb_id = request.data.get("jobb_id")
        if not jobb_id:
            return Response(
                {"error": "jobb_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Handle multiple files
        files = request.FILES.getlist("files")
        names = request.data.getlist("names", [])

        if not files:
            return Response(
                {"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        created_files = []
        errors = []

        for i, file in enumerate(files):
            # Use provided name or default to filename
            name = names[i] if i < len(names) else file.name

            try:
                job_file = JobberFile.objects.create(jobb=jobb, file=file, name=name)
                created_files.append(
                    {
                        "id": job_file.id,
                        "name": job_file.name,
                        "filename": file.name,
                        "size": file.size,
                    }
                )
            except Exception as e:
                errors.append({"filename": file.name, "error": str(e)})

        return Response(
            {
                "message": f"{len(created_files)} files uploaded successfully",
                "jobb_id": jobb_id,
                "uploaded": created_files,
                "errors": errors,
                "total_files": JobberFile.objects.filter(jobb=jobb).count(),
            },
            status=(
                status.HTTP_201_CREATED
                if created_files
                else status.HTTP_400_BAD_REQUEST
            ),
        )

    @action(detail=False, methods=["get"])
    def file_types(self, request):
        """
        Get summary of file types across all jobs or for a specific job.
        Query params: jobb_id (optional)
        """
        jobb_id = request.query_params.get("jobb_id")
        queryset = JobberFile.objects.all()

        if jobb_id:
            try:
                jobb = Jobber.objects.get(ordre_nr=jobb_id)
                queryset = queryset.filter(jobb=jobb)
            except Jobber.DoesNotExist:
                return Response(
                    {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Analyze file types
        file_types = {}
        total_size = 0

        for job_file in queryset:
            if job_file.file and hasattr(job_file.file, "name"):
                extension = (
                    job_file.file.name.split(".")[-1].lower()
                    if "." in job_file.file.name
                    else "unknown"
                )

                if extension not in file_types:
                    file_types[extension] = {"count": 0, "total_size": 0}

                file_types[extension]["count"] += 1
                if hasattr(job_file.file, "size"):
                    file_size = job_file.file.size
                    file_types[extension]["total_size"] += file_size
                    total_size += file_size

        return Response(
            {
                "summary": {
                    "total_files": queryset.count(),
                    "total_size_bytes": total_size,
                    "file_types_count": len(file_types),
                },
                "file_types": file_types,
                "jobb_id": jobb_id,
            }
        )


class JobberTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks associated with jobs (Jobber)."""

    queryset = JobberTask.objects.all().order_by("-created_at")
    serializer_class = JobberTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = JobberTaskFilter
    search_fields = ["title", "notes", "jobb__tittel"]

    def get_queryset(self):
        """Optimize queryset with select_related."""
        return JobberTask.objects.select_related("jobb").order_by("-created_at")

    @action(detail=False, methods=["get"])
    def by_job(self, request):
        """
        Get all tasks for a specific job.
        Query params: jobb_id (ordre_nr)
        """
        jobb_id = request.query_params.get("jobb_id")
        if not jobb_id:
            return Response(
                {"error": "jobb_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        tasks = JobberTask.objects.filter(jobb=jobb).order_by("-created_at")
        serializer = self.get_serializer(tasks, many=True)

        # Calculate stats
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(completed=True).count()
        pending_tasks = total_tasks - completed_tasks

        return Response(
            {
                "jobb": {"ordre_nr": jobb.ordre_nr, "tittel": jobb.tittel},
                "stats": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "pending": pending_tasks,
                    "completion_rate": (
                        round((completed_tasks / total_tasks) * 100, 1)
                        if total_tasks > 0
                        else 0
                    ),
                },
                "tasks": serializer.data,
            }
        )

    @action(detail=True, methods=["post"])
    def toggle_complete(self, request, pk=None):
        """
        Toggle the completed status of a task.
        Returns: Updated task data
        """
        task = self.get_object()

        # Toggle completed status
        task.completed = not task.completed
        task.save()

        serializer = self.get_serializer(task)
        return Response(
            {
                "message": f"Task marked as {'completed' if task.completed else 'pending'}",
                "task": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def bulk_complete(self, request):
        """
        Mark multiple tasks as completed or pending.
        Expects: {"task_ids": [1, 2, 3], "completed": true}
        """
        task_ids = request.data.get("task_ids", [])
        completed = request.data.get("completed", True)

        if not task_ids:
            return Response(
                {"error": "task_ids list cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_count = JobberTask.objects.filter(id__in=task_ids).update(
            completed=completed
        )

        return Response(
            {
                "message": f"{updated_count} tasks marked as {'completed' if completed else 'pending'}",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


class TimelisteViewSet(viewsets.ModelViewSet):
    queryset = Timeliste.objects.all().order_by("-created_at")
    serializer_class = TimelisteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TimelisteFilter
    search_fields = ["beskrivelse", "jobb__tittel", "user__username"]

    def perform_create(self, serializer):
        """Automatically set the user from the request."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def user_stats(self, request):
        """
        Get time tracking statistics for the current user and all users.
        Returns: {
            "today": {"hours": 8.5, "entries": 3},
            "yesterday": {"hours": 7.0, "entries": 2},
            "total_user": {"hours": 245.5, "entries": 89},
            "total_all_users": {"hours": 1847.5, "entries": 567}
        }
        """
        from datetime import timedelta
        from django.db.models import Sum

        user = request.user
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)

        # Today's stats
        today_entries = Timeliste.objects.filter(user=user, dato=today)
        today_hours = today_entries.aggregate(Sum("timer"))["timer__sum"] or 0
        today_count = today_entries.count()

        # Yesterday's stats
        yesterday_entries = Timeliste.objects.filter(user=user, dato=yesterday)
        yesterday_hours = yesterday_entries.aggregate(Sum("timer"))["timer__sum"] or 0
        yesterday_count = yesterday_entries.count()

        # Total user stats
        user_entries = Timeliste.objects.filter(user=user)
        total_user_hours = user_entries.aggregate(Sum("timer"))["timer__sum"] or 0
        total_user_count = user_entries.count()

        # Total all users stats
        all_entries = Timeliste.objects.all()
        total_all_hours = all_entries.aggregate(Sum("timer"))["timer__sum"] or 0
        total_all_count = all_entries.count()

        return Response(
            {
                "today": {"hours": float(today_hours), "entries": today_count},
                "yesterday": {
                    "hours": float(yesterday_hours),
                    "entries": yesterday_count,
                },
                "total_user": {
                    "hours": float(total_user_hours),
                    "entries": total_user_count,
                },
                "total_all_users": {
                    "hours": float(total_all_hours),
                    "entries": total_all_count,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def by_date(self, request):
        """
        Get time entries grouped by date for the current user.
        Query params:
        - start_date: Start date (YYYY-MM-DD, optional)
        - end_date: End date (YYYY-MM-DD, optional)
        - user_id: User ID (optional, defaults to current user)
        - jobb: Job ID (optional, filters by specific job)
        """
        from datetime import datetime
        from django.db.models import Sum

        user = request.user
        user_id = request.query_params.get("user_id")

        # Allow filtering by different user if user_id is provided
        if user_id:
            try:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": f"User with id {user_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        queryset = Timeliste.objects.filter(user=user)

        # Filter by job if jobb parameter is provided
        jobb_id = request.query_params.get("jobb")
        if jobb_id:
            try:
                jobb = Jobber.objects.get(ordre_nr=jobb_id)
                queryset = queryset.filter(jobb=jobb)
            except Jobber.DoesNotExist:
                return Response(
                    {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Apply date filters
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                queryset = queryset.filter(dato__gte=start_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                queryset = queryset.filter(dato__lte=end_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Group by date
        entries_by_date = {}
        for entry in queryset.select_related("jobb", "user").order_by("dato"):
            date_str = str(entry.dato) if entry.dato else "no_date"

            if date_str not in entries_by_date:
                entries_by_date[date_str] = {
                    "date": date_str,
                    "total_hours": 0,
                    "entries": [],
                }

            entries_by_date[date_str]["total_hours"] += entry.timer or 0
            entries_by_date[date_str]["entries"].append(
                {
                    "id": entry.id,
                    "beskrivelse": entry.beskrivelse,
                    "timer": entry.timer,
                    "jobb_tittel": entry.jobb.tittel if entry.jobb else None,
                    "jobb_id": entry.jobb.ordre_nr if entry.jobb else None,
                    "created_at": entry.created_at,
                }
            )

        # Convert to list and sort by date
        result = sorted(entries_by_date.values(), key=lambda x: x["date"], reverse=True)

        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "total_dates": len(result),
                "entries_by_date": result,
            }
        )


class ActiveTimerSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing active timer sessions.
    Provides endpoints to start, stop, ping, and retrieve active timers.
    """

    queryset = ActiveTimerSession.objects.all().select_related("user", "jobb")
    serializer_class = ActiveTimerSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to show only the current user's sessions."""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def start(self, request):
        """
        Start a new timer session.
        Expects: {"jobb": ordre_nr}
        Returns: Created session data
        """
        jobb_id = request.data.get("jobb")

        if not jobb_id:
            return Response(
                {"error": "jobb field is required (ordre_nr)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already has an active session
        existing_session = ActiveTimerSession.objects.filter(user=request.user).first()
        if existing_session:
            return Response(
                {
                    "error": "You already have an active timer session",
                    "active_session": ActiveTimerSessionSerializer(
                        existing_session
                    ).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate job exists
        try:
            jobb = Jobber.objects.get(ordre_nr=jobb_id)
        except Jobber.DoesNotExist:
            return Response(
                {"error": f"Job with ordre_nr '{jobb_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create new session
        session = ActiveTimerSession.objects.create(user=request.user, jobb=jobb)

        serializer = self.get_serializer(session)
        return Response(
            {
                "message": "Timer started successfully",
                "session": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def _round_to_nearest_half_hour(self, minutes):
        """
        Round minutes to nearest 30-minute increment with 10-minute tolerance.
        - If time > 10 minutes over nearest 30-min mark → round up
        - If time ≤ 10 minutes over → round down
        - Result is always X.0h or X.5h (30-minute increments)
        - Minimum: 30 minutes
        """
        if minutes < 30:
            return 30  # Minimum 30 minutes

        lower_mark = (minutes // 30) * 30
        upper_mark = lower_mark + 30
        minutes_over = minutes - lower_mark

        if minutes_over <= 10:
            return lower_mark
        else:
            return upper_mark

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        """
        Stop an active timer session and create a time entry.
        Accepts optional elapsed_seconds parameter to use adjusted time from frontend.
        Returns: Created Timeliste entry
        """
        session = self.get_object()

        # Use provided elapsed_seconds if available, otherwise calculate from start_time
        elapsed_seconds = request.data.get("elapsed_seconds")
        if elapsed_seconds is not None:
            # Use the adjusted time from frontend
            try:
                elapsed_seconds = int(elapsed_seconds)
            except (ValueError, TypeError):
                return Response(
                    {"error": "elapsed_seconds must be a valid integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Calculate from start_time as before
            elapsed_seconds = session.elapsed_seconds

        # Convert to minutes and apply rounding logic
        elapsed_minutes = round(elapsed_seconds / 60)
        rounded_minutes = self._round_to_nearest_half_hour(elapsed_minutes)
        rounded_hours = rounded_minutes / 60  # Convert to hours (e.g., 1.5h)

        # Get optional description from request
        beskrivelse = request.data.get("beskrivelse", "")

        # Create Timeliste entry with rounded time stored as minutes
        # Note: timer field stores minutes as SmallIntegerField
        timeliste = Timeliste.objects.create(
            user=session.user,
            jobb=session.jobb,
            beskrivelse=beskrivelse,
            dato=timezone.now().date(),
            timer=rounded_minutes,  # Store minutes (30, 60, 90, 120, etc.)
        )

        # Delete the session
        session.delete()

        # Return the created time entry
        from .serializers import TimelisteSerializer

        serializer = TimelisteSerializer(timeliste)
        return Response(
            {
                "message": "Timer stopped successfully",
                "elapsed_seconds": elapsed_seconds,
                "elapsed_minutes": elapsed_minutes,
                "rounded_minutes": rounded_minutes,
                "rounded_hours": rounded_hours,
                "timeliste": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def active(self, request):
        """
        Get the current user's active timer session.
        Returns: Session data or null if no active session
        """
        session = ActiveTimerSession.objects.filter(user=request.user).first()

        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        else:
            return Response(None, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def ping(self, request, pk=None):
        """
        Update the last_ping timestamp for a session.
        Used as a heartbeat to track active sessions.
        Returns: Updated session data
        """
        session = self.get_object()

        # The last_ping field has auto_now=True, so just save to update it
        session.save()

        serializer = self.get_serializer(session)
        return Response(
            {
                "message": "Ping successful",
                "session": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """
        Pause an active timer session.
        Returns: Updated session data
        """
        session = self.get_object()

        if session.is_paused:
            return Response(
                {"error": "Timer is already paused"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as paused and record when
        session.is_paused = True
        session.paused_at = timezone.now()
        session.save()

        serializer = self.get_serializer(session)
        return Response(
            {
                "message": "Timer paused successfully",
                "session": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """
        Resume a paused timer session.
        Returns: Updated session data
        """
        session = self.get_object()

        if not session.is_paused:
            return Response(
                {"error": "Timer is not paused"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate how long it was paused and add to total
        if session.paused_at:
            pause_duration = int((timezone.now() - session.paused_at).total_seconds())
            session.total_paused_seconds += pause_duration

        # Resume the timer
        session.is_paused = False
        session.paused_at = None
        session.save()

        serializer = self.get_serializer(session)
        return Response(
            {
                "message": "Timer resumed successfully",
                "session": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
