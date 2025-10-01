# Location-Based Job Entry Requirements

**Added:** 2025-10-01
**Priority:** High
**Frontend Feature:** Auto-entry to nearby jobs based on GPS location
**Status:** Frontend implementation complete, awaiting backend optimization

---

## 🎯 Problem Statement

The frontend currently implements location-based job proximity detection, but it's **inefficient**:

- Geocodes every job's address on-demand (20 jobs = 20 API calls to Kartverket)
- Each auto-entry check takes 4-10 seconds
- Same addresses get geocoded repeatedly
- Risk of rate limiting from Kartverket API
- Poor user experience with long wait times

## ✅ Solution: Backend Geocoding & Storage

Store geocoded coordinates in the database and provide a proximity search endpoint.

---

## 1. Database Schema Changes

### Job Model Updates

Add geocoding fields to the `Job` model:

```python
class Job(models.Model):
    # Existing fields
    ordre_nr = models.CharField(max_length=10, primary_key=True)
    tittel = models.CharField(max_length=200, blank=True)
    adresse = models.CharField(max_length=200, blank=True)
    telefon_nr = models.CharField(max_length=20, blank=True)
    beskrivelse = models.TextField(blank=True)
    ferdig = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW GEOCODING FIELDS
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Latitude coordinate from geocoded address"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Longitude coordinate from geocoded address"
    )
    geocoded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when address was last geocoded"
    )
    geocode_accuracy = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ('exact', 'Exact Match'),
            ('approximate', 'Approximate Match'),
            ('failed', 'Geocoding Failed'),
        ],
        help_text="Quality of geocoding result"
    )
```

### Database Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=['latitude', 'longitude']),
        models.Index(fields=['ferdig', 'latitude', 'longitude']),
    ]
```

---

## 2. Geocoding Service

Create `services/geocoding.py`:

```python
import requests
from typing import Optional
from django.core.cache import cache

class GeocodingService:
    """Service for geocoding Norwegian addresses using Kartverket API"""

    KARTVERKET_SEARCH_URL = "https://ws.geonorge.no/adresser/v1/sok"
    CACHE_TIMEOUT = 86400 * 30  # 30 days

    @classmethod
    def geocode_address(cls, address: str) -> Optional[dict]:
        """
        Geocode a Norwegian address

        Returns:
            dict: {'lat': float, 'lon': float, 'accuracy': str}
            None: if geocoding failed
        """
        if not address or not address.strip():
            return None

        # Check cache first
        cache_key = f"geocode:{address.lower().strip()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            response = requests.get(
                cls.KARTVERKET_SEARCH_URL,
                params={'sok': address, 'treffPerSide': 1},
                timeout=5
            )

            if not response.ok:
                return None

            data = response.json()

            if data.get('adresser') and len(data['adresser']) > 0:
                address_data = data['adresser'][0]

                if address_data.get('representasjonspunkt'):
                    result = {
                        'lat': address_data['representasjonspunkt']['lat'],
                        'lon': address_data['representasjonspunkt']['lon'],
                        'accuracy': 'exact'
                    }
                    cache.set(cache_key, result, cls.CACHE_TIMEOUT)
                    return result

            return None

        except Exception as e:
            print(f"Geocoding error for '{address}': {e}")
            return None

    @classmethod
    def calculate_distance(cls, lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
        """Calculate distance between coordinates (Haversine formula)"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371e3  # Earth's radius in meters

        φ1 = radians(lat1)
        φ2 = radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lon2 - lon1)

        a = sin(Δφ/2) * sin(Δφ/2) + \
            cos(φ1) * cos(φ2) * sin(Δλ/2) * sin(Δλ/2)
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c  # meters
```

---

## 3. Auto-Geocoding Signal Handler

Create `signals.py` to auto-geocode on save:

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Job
from .services.geocoding import GeocodingService
from django.utils import timezone

@receiver(pre_save, sender=Job)
def geocode_job_address(sender, instance, **kwargs):
    """Auto-geocode job address when created or address changes"""

    # Check if address changed
    try:
        old_instance = Job.objects.get(pk=instance.pk)
        address_changed = old_instance.adresse != instance.adresse
    except Job.DoesNotExist:
        address_changed = True  # New job

    if address_changed and instance.adresse and instance.adresse.strip():
        result = GeocodingService.geocode_address(instance.adresse)

        if result:
            instance.latitude = result['lat']
            instance.longitude = result['lon']
            instance.geocoded_at = timezone.now()
            instance.geocode_accuracy = result['accuracy']
        else:
            instance.latitude = None
            instance.longitude = None
            instance.geocode_accuracy = 'failed'
            instance.geocoded_at = timezone.now()
```

---

## 4. API Endpoint: Nearby Jobs

### Endpoint Specification

**URL:** `GET /api/memo/jobs/nearby/`

**Query Parameters:**

- `lat` (required): User's latitude
- `lon` (required): User's longitude
- `radius` (optional, default=100): Search radius in meters
- `ferdig` (optional): Filter by completion status

**Response Format:**

```json
[
  {
    "ordre_nr": "8001",
    "tittel": "Electrical Installation",
    "adresse": "Stortingsgata 4, 0158 OSLO",
    "telefon_nr": "+47 123 45 678",
    "beskrivelse": "Install electrical panel",
    "ferdig": false,
    "latitude": 59.9133,
    "longitude": 10.7389,
    "geocoded_at": "2025-10-01T12:00:00Z",
    "geocode_accuracy": "exact",
    "distance": 45.2,
    "total_hours": 12.5,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:45:00Z"
  }
]
```

### Serializer Updates

```python
from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'ordre_nr', 'tittel', 'adresse', 'telefon_nr',
            'beskrivelse', 'ferdig', 'latitude', 'longitude',
            'geocoded_at', 'geocode_accuracy', 'distance',
            'total_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'latitude', 'longitude',
            'geocoded_at', 'geocode_accuracy'
        ]

    def get_distance(self, obj):
        """Calculate distance if user coords provided"""
        user_lat = self.context.get('user_lat')
        user_lon = self.context.get('user_lon')

        if user_lat and user_lon and obj.latitude and obj.longitude:
            from .services.geocoding import GeocodingService
            return round(GeocodingService.calculate_distance(
                user_lat, user_lon, obj.latitude, obj.longitude
            ), 1)
        return None
```

### ViewSet Implementation

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer
from .services.geocoding import GeocodingService

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get jobs near a location"""
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lon = float(request.query_params.get('lon'))
        except (TypeError, ValueError):
            return Response(
                {'error': 'lat and lon are required and must be numbers'},
                status=400
            )

        radius = float(request.query_params.get('radius', 100))
        ferdig = request.query_params.get('ferdig')

        # Filter jobs with coordinates
        queryset = self.queryset.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )

        if ferdig is not None:
            queryset = queryset.filter(ferdig=ferdig.lower() == 'true')

        # Calculate distances and filter by radius
        nearby_jobs = []
        for job in queryset:
            distance = GeocodingService.calculate_distance(
                user_lat, user_lon,
                float(job.latitude), float(job.longitude)
            )

            if distance <= radius:
                nearby_jobs.append({'job': job, 'distance': distance})

        # Sort by distance
        nearby_jobs.sort(key=lambda x: x['distance'])

        # Serialize with distance
        serializer = self.get_serializer(
            [item['job'] for item in nearby_jobs],
            many=True,
            context={'user_lat': user_lat, 'user_lon': user_lon}
        )

        return Response(serializer.data)
```

---

## 5. Management Command: Bulk Geocoding

Create `management/commands/geocode_jobs.py`:

```python
from django.core.management.base import BaseCommand
from memo.models import Job
from memo.services.geocoding import GeocodingService
from django.utils import timezone

class Command(BaseCommand):
    help = 'Geocode all jobs with addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode all jobs even if already geocoded',
        )

    def handle(self, *args, **options):
        force = options['force']

        if force:
            jobs = Job.objects.filter(
                adresse__isnull=False
            ).exclude(adresse='')
        else:
            jobs = Job.objects.filter(
                adresse__isnull=False,
                latitude__isnull=True
            ).exclude(adresse='')

        total = jobs.count()
        success = 0
        failed = 0

        self.stdout.write(f"Found {total} jobs to geocode...")

        for job in jobs:
            result = GeocodingService.geocode_address(job.adresse)

            if result:
                job.latitude = result['lat']
                job.longitude = result['lon']
                job.geocoded_at = timezone.now()
                job.geocode_accuracy = result['accuracy']
                job.save()
                success += 1
                self.stdout.write(f"✓ {job.ordre_nr}: {job.adresse}")
            else:
                job.geocode_accuracy = 'failed'
                job.geocoded_at = timezone.now()
                job.save()
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"✗ {job.ordre_nr}: Failed"
                    )
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nComplete: {success} succeeded, {failed} failed"
        ))
```

---

## 6. Migration & Deployment

```bash
# Create migration
python manage.py makemigrations memo

# Apply migration
python manage.py migrate memo

# Geocode existing jobs
python manage.py geocode_jobs

# Force re-geocode all
python manage.py geocode_jobs --force
```

---

## 7. Performance Benefits

### Before (Current Frontend Implementation)

- 20 jobs = 20 Kartverket API calls
- Average response time: **4-10 seconds**
- No caching
- Rate limiting risk
- Poor mobile experience

### After (Backend Implementation)

- 20 jobs = **1 database query**
- Average response time: **< 100ms**
- 30-day caching
- No rate limiting issues
- Instant mobile response

**Performance Improvement: ~100x faster** 🚀

---

## 8. Frontend Integration

Once backend is deployed, frontend will update to:

```typescript
// Before: Geocode all jobs client-side (slow)
const nearbyJobs = await Promise.all(
  jobs.map((job) => geocodeAndCalculateDistance(job))
);

// After: Single API call (fast)
const nearbyJobs = await jobsAPI.getNearbyJobs({
  lat: location.latitude,
  lon: location.longitude,
  radius: 100,
});
```

Frontend will maintain fallback to client-side geocoding for backward compatibility.

---

## 9. Testing Checklist

- [ ] Unit test: `GeocodingService.geocode_address()`
- [ ] Unit test: `GeocodingService.calculate_distance()`
- [ ] Integration test: Job auto-geocoding signal
- [ ] API test: `/nearby/` endpoint with various radii
- [ ] API test: Invalid coordinates handling
- [ ] Performance test: 1000+ jobs proximity search
- [ ] Cache test: Verify 30-day caching works
- [ ] Migration test: Existing jobs geocoded correctly

---

## 10. Additional Features (Optional)

### Heatmap Data Endpoint

```python
@action(detail=False, methods=['get'])
def heatmap(self, request):
    """Get job locations for heatmap visualization"""
    jobs = self.queryset.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )

    return Response([
        {
            'lat': float(job.latitude),
            'lon': float(job.longitude),
            'ordre_nr': job.ordre_nr,
            'tittel': job.tittel,
            'ferdig': job.ferdig
        }
        for job in jobs
    ])
```

### Geofencing Alerts

- Notify users when entering/leaving job radius
- Automatic time tracking when near job location
- Push notifications for nearby incomplete jobs

---

## 📋 Implementation Priority

**Priority:** High
**Estimated Effort:** 4-6 hours
**Dependencies:** None
**Frontend Impact:** Major UX improvement

### Implementation Steps

1. **Day 1:** Database migration + geocoding service (2 hours)
2. **Day 1:** Signal handler + bulk command (1 hour)
3. **Day 2:** API endpoint + serializer (2 hours)
4. **Day 2:** Testing + deployment (1 hour)

---

## 🔗 Related Resources

- **Kartverket API Docs:** https://ws.geonorge.no/adresser/v1/
- **Frontend Implementation:** `src/app/memo/page.tsx:242-333`
- **TypeScript Types:** `src/lib/api/memo/types.ts:54-65`

---

_Updated: 2025-10-01 - Location-based features_
