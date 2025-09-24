from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, JobberImage, JobberFile, Timeliste
from .serializers import (
    LeverandorerSerializer,
    LeverandorerCreateSerializer,
    MatriellSerializer,
    MatriellBulkCreateSerializer,
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

    def get_serializer_class(self):
        if self.action == 'bulk_create':
            return LeverandorerCreateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create manufacturers from EFObasen data
        Expects list of manufacturer objects
        """
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected a list of manufacturer objects"},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = {
            'created': 0,
            'updated': 0,
            'errors': []
        }

        with transaction.atomic():
            for i, item in enumerate(request.data):
                try:
                    # Check if manufacturer already exists
                    existing = Leverandorer.objects.filter(name=item.get('name')).first()
                    if existing:
                        # Update existing
                        serializer = self.get_serializer(existing, data=item, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            results['updated'] += 1
                        else:
                            results['errors'].append(f"Item {i}: {serializer.errors}")
                    else:
                        # Create new
                        serializer = self.get_serializer(data=item)
                        if serializer.is_valid():
                            serializer.save()
                            results['created'] += 1
                        else:
                            results['errors'].append(f"Item {i}: {serializer.errors}")

                except Exception as e:
                    results['errors'].append(f"Item {i}: {str(e)}")

        return Response(results, status=status.HTTP_201_CREATED)


class MatriellViewSet(viewsets.ModelViewSet):
    queryset = Matriell.objects.all().order_by("-created_at")
    serializer_class = MatriellSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'bulk_create':
            return MatriellBulkCreateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create electrical components from EFObasen data
        Accepts both single objects and lists of objects
        """
        data = request.data
        if not isinstance(data, list):
            data = [data]

        results = {
            'created': 0,
            'updated': 0,
            'errors': [],
            'total_processed': len(data)
        }

        with transaction.atomic():
            for i, item in enumerate(data):
                try:
                    el_nr = item.get('el_nr')
                    if not el_nr:
                        results['errors'].append(f"Item {i}: Missing el_nr")
                        continue

                    # Check if product already exists
                    existing = Matriell.objects.filter(el_nr=el_nr).first()
                    if existing:
                        # Update existing
                        serializer = self.get_serializer(existing, data=item, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            results['updated'] += 1
                        else:
                            results['errors'].append(f"Item {i} (el_nr: {el_nr}): {serializer.errors}")
                    else:
                        # Create new
                        serializer = self.get_serializer(data=item)
                        if serializer.is_valid():
                            serializer.save()
                            results['created'] += 1
                        else:
                            results['errors'].append(f"Item {i} (el_nr: {el_nr}): {serializer.errors}")

                except Exception as e:
                    results['errors'].append(f"Item {i}: {str(e)}")

        # Determine response status
        if results['errors']:
            response_status = status.HTTP_207_MULTI_STATUS  # Partial success
        else:
            response_status = status.HTTP_201_CREATED

        return Response(results, status=response_status)

    @action(detail=False, methods=['post'])
    def efobasen_import(self, request):
        """
        Import single product from EFObasen structured data
        Expects the structured JSON format from n8n workflow
        """
        try:
            # Extract el_nr from different possible locations
            el_nr = None
            if 'elnummer' in request.data:
                el_nr = request.data['elnummer']
            elif 'el_nr' in request.data:
                el_nr = request.data['el_nr']

            if not el_nr:
                return Response(
                    {"error": "Missing el_nr or elnummer in data"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Transform EFObasen data to our model format
            matriell_data = {
                'el_nr': el_nr,
                'tittel': request.data.get('produktnavn', ''),
                'info': request.data.get('beskrivelse', ''),
                'ean_number': request.data.get('gtin', ''),
                'article_number': request.data.get('leverandor_nummer', ''),
                'norwegian_description': request.data.get('produktnavn_lang', ''),
                'english_description': request.data.get('produktnavn_lang_eng', ''),
                'height': request.data.get('hoyde', ''),
                'width': request.data.get('bredde', ''),
                'depth': request.data.get('lengde', ''),
                'weight': request.data.get('vekt', ''),
                'etim_class': request.data.get('etim_class', ''),
                'approved': True,
                'discontinued': False,
                'in_stock': request.data.get('lagerfores', '').lower() != 'nei',
                'leverandor_name': request.data.get('produsent', ''),
            }

            # Handle document URLs
            dokumenter = request.data.get('dokumenter', {})
            if dokumenter.get('datablad'):
                # Clean up the API endpoint URL
                datasheet = dokumenter['datablad'].strip('[]')
                if not datasheet.startswith('http'):
                    datasheet = f"https://efobasen.efo.no{datasheet}"
                matriell_data['datasheet_url'] = datasheet

            # Handle image URL
            bilde = request.data.get('bilde', '')
            if bilde:
                bilde = bilde.strip('[]')
                if not bilde.startswith('http'):
                    bilde = f"https://efobasen.efo.no{bilde}"
                matriell_data['image_url'] = bilde

            # Use bulk_create logic for single item
            return self.bulk_create(type('Request', (), {'data': [matriell_data]})())

        except Exception as e:
            return Response(
                {"error": f"Failed to process EFObasen data: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
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
