# Memo App API Documentation

## Overview
The Memo App provides a comprehensive REST API for managing Norwegian electrical components, jobs, suppliers, and time tracking. This API is optimized for frontend applications handling large datasets (20,000+ items) with advanced search, filtering, and bulk operations.

## Base URL
```
https://api.nxfs.no/app/memo/
```

## Authentication
All endpoints require authentication. Include the authorization header:
```
Authorization: Token <your-api-token>
```

## Table of Contents
1. [Dashboard Endpoints](#dashboard-endpoints)
2. [Materials (Matriell)](#materials-matriell)
3. [Electrical Categories](#electrical-categories-elektrisk-kategorier)
4. [Suppliers (Leverandører)](#suppliers-leverandører)
5. [Jobs (Jobber)](#jobs-jobber)
6. [Job Materials](#job-materials-jobbmatriell)
7. [Job Images](#job-images)
8. [Job Files](#job-files)
9. [Time Tracking (Timeliste)](#time-tracking-timeliste)
10. [Search & Filtering](#search--filtering)
11. [Error Handling](#error-handling)

---

## Dashboard Endpoints

### Get Overall Statistics
```http
GET /dashboard/stats/
```

**Response:**
```json
{
  "materials": {
    "total": 15420,
    "favorites": 234,
    "approved": 14890,
    "in_stock": 13245,
    "discontinued": 178,
    "approval_rate": 96.6
  },
  "jobs": {
    "total": 892,
    "completed": 743,
    "active": 149,
    "completion_rate": 83.3,
    "total_hours": 2847.5
  },
  "suppliers": {
    "total": 127,
    "with_materials": 98,
    "utilization_rate": 77.2
  },
  "categories": {
    "total": 45,
    "with_materials": 42,
    "utilization_rate": 93.3
  },
  "time_tracking": {
    "total_entries": 1847,
    "entries_this_month": 234
  }
}
```

### Get Recent Activities
```http
GET /dashboard/recent/
```

**Response:**
```json
{
  "materials": [
    {
      "id": 14,
      "el_nr": "1000001",
      "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5",
      "varemerke": "LAPP KABEL",
      "leverandor_name": "LAPP KABEL AS",
      "created_at": "2025-01-26T10:30:00+02:00"
    }
  ],
  "jobs": [
    {
      "id": "JOB-2025-001",
      "tittel": "Electrical installation Oslo",
      "ferdig": false,
      "created_at": "2025-01-26T09:15:00+02:00"
    }
  ],
  "time_entries": [
    {
      "id": 567,
      "beskrivelse": "Cable installation work",
      "timer": 8.5,
      "dato": "2025-01-26",
      "jobb_tittel": "Electrical installation Oslo",
      "user": "john_doe",
      "created_at": "2025-01-26T16:30:00+02:00"
    }
  ]
}
```

### Get Quick Access Items
```http
GET /dashboard/quick_access/
```

**Response:**
```json
{
  "popular_materials": [
    {
      "id": 42,
      "el_nr": "1000042",
      "tittel": "Popular Cable Type",
      "usage_count": 15,
      "leverandor_name": "NEXANS"
    }
  ],
  "favorite_materials": [...],
  "active_jobs": [...],
  "popular_suppliers": [...]
}
```

---

## Materials (Matriell)

### List Materials
```http
GET /matriell/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `search`: Search across multiple fields
- `el_nr`: Filter by electrical number
- `tittel`: Filter by title
- `varemerke`: Filter by brand
- `approved`: Filter by approval status (true/false)
- `favorites`: Filter favorites (true/false)
- `in_stock`: Filter stock status (true/false)
- `kategori_blokknummer`: Filter by category block number
- `leverandor_name`: Filter by supplier name
- `ordering`: Order results (e.g., "-created_at", "el_nr")

**Example:**
```http
GET /matriell/?search=cable&approved=true&page=1
```

**Response:**
```json
{
  "count": 1247,
  "next": "https://api.nxfs.no/app/memo/matriell/?page=2",
  "previous": null,
  "results": [
    {
      "id": 14,
      "el_nr": "1000001",
      "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5",
      "varemerke": "LAPP KABEL",
      "varenummer": "0012504",
      "gtin_number": "4044774012504",
      "info": "Flexible control cable for industrial applications",
      "teknisk_beskrivelse": "3x2.5mm² + 3x0.5mm² earth wire",
      "varebetegnelse": "Control cable",
      "hoyde": 12.5,
      "bredde": 8.2,
      "lengde": null,
      "vekt": 245,
      "bilder": "https://example.com/image.jpg",
      "produktblad": "https://example.com/datasheet.pdf",
      "produkt_url": "https://example.com/product",
      "fdv": "Maintenance info",
      "cpr_sertifikat": "CPR certificate info",
      "miljoinformasjon": "Environmental information",
      "approved": true,
      "discontinued": false,
      "in_stock": true,
      "favorites": false,
      "leverandor": {
        "id": 5,
        "navn": "LAPP KABEL AS",
        "telefon": "+47 12345678",
        "hjemmeside": "https://lappkabel.no",
        "addresse": "Industrial Street 123",
        "poststed": "Oslo",
        "postnummer": "0123",
        "epost": "info@lappkabel.no"
      },
      "kategori": {
        "id": 2,
        "blokknummer": "10",
        "kategori": "Kabler og ledninger",
        "beskrivelse": "All types of cables and wires"
      },
      "created_at": "2025-01-26T10:30:00+02:00",
      "updated_at": "2025-01-26T10:30:00+02:00"
    }
  ]
}
```

### Get Material by ID
```http
GET /matriell/{id}/
```

### Quick Material Lookup
```http
GET /matriell/lookup/?el_nr=1000001
```

**Response:**
```json
{
  "id": 14,
  "el_nr": "1000001",
  "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5",
  // ... full material data
}
```

### Material Choices (for Dropdowns)
```http
GET /matriell/choices/?search=cable&limit=50
```

**Response:**
```json
[
  {
    "id": 14,
    "el_nr": "1000001",
    "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5"
  },
  // ... up to 50 items
]
```

### Manage Favorites

#### Check Favorite Status
```http
GET /matriell/{id}/favorite/
```

#### Add to Favorites
```http
POST /matriell/{id}/favorite/
```

#### Remove from Favorites
```http
DELETE /matriell/{id}/favorite/
```

#### List All Favorites
```http
GET /matriell/favorites/?page=1&page_size=50
```

### Bulk Operations
```http
POST /matriell/bulk_operations/
```

**Request Body:**
```json
{
  "action": "update_status",
  "el_nrs": ["1000001", "1000002", "1000003"],
  "data": {
    "approved": true,
    "in_stock": false
  }
}
```

**Available Actions:**
- `update_status`: Update approval, stock, discontinued, favorites
- `delete`: Mark as discontinued
- `approve`: Bulk approve materials
- `set_stock`: Update stock status

**Response:**
```json
{
  "message": "Updated 3 materials",
  "affected_count": 3,
  "action": "update_status",
  "updated_fields": ["approved", "in_stock"]
}
```

### Bulk Favorites Management
```http
POST /matriell/bulk_favorite/
```

**Request Body:**
```json
{
  "action": "add",
  "el_nrs": ["1000001", "1000002", "1000003"]
}
```

### Data Validation
```http
POST /matriell/validate_data/
```

**Request Body:**
```json
{
  "el_nr": "1000001",
  "tittel": "Test Material",
  "leverandor": "NEXANS",
  "kategori": "10"
}
```

**Response:**
```json
{
  "valid": false,
  "errors": [
    "Material with el_nr '1000001' already exists (ID: 14)"
  ],
  "warnings": [
    "Field 'hoyde' has negative value: -5.0"
  ],
  "data_summary": {
    "el_nr": "1000001",
    "tittel": "Test Material",
    "leverandor": "NEXANS",
    "kategori": "10",
    "has_gtin": false
  }
}
```

### Check Duplicates
```http
GET /matriell/check_duplicates/?el_nr=1000001
GET /matriell/check_duplicates/?gtin_number=1234567890
GET /matriell/check_duplicates/?tittel=cable&limit=10
```

### EFO Basen Import
```http
POST /matriell/efobasen_import/
```

**Request Body:**
```json
{
  "el_nr": "1000001",
  "tittel": "ÖLFLEX® Cable",
  "varemerke": "LAPP KABEL",
  "leverandor": {
    "navn": "LAPP KABEL AS",
    "telefon": "+47 12345678"
  },
  "kategori": "10"
}
```

---

## Electrical Categories (Elektrisk Kategorier)

### List Categories
```http
GET /elektrisk-kategorier/
```

**Query Parameters:**
- `search`: Search categories
- `blokknummer`: Filter by block number
- `kategori`: Filter by category name
- `ordering`: Order results

### Category Choices
```http
GET /elektrisk-kategorier/choices/?search=kabel&limit=50
```

**Response:**
```json
[
  {
    "id": 2,
    "kategori": "Kabler og ledninger",
    "blokknummer": "10"
  }
]
```

---

## Suppliers (Leverandører)

### List Suppliers
```http
GET /leverandorer/
```

### Supplier Lookup
```http
GET /leverandorer/lookup/?name=nexans
```

### Supplier Choices
```http
GET /leverandorer/choices/?search=nexans&limit=50
```

**Response:**
```json
[
  {
    "id": 5,
    "name": "NEXANS NORWAY AS"
  }
]
```

---

## Jobs (Jobber)

### List Jobs
```http
GET /jobber/
```

**Query Parameters:**
- `search`: Search jobs
- `tittel`: Filter by title
- `ferdig`: Filter by completion status
- `created_after`: Filter by creation date
- `ordering`: Order results

### Job Lookup
```http
GET /jobber/lookup/?ordre_nr=JOB-2025-001
```

### Add Materials to Job
```http
POST /jobber/{ordre_nr}/add_materials/
```

**Request Body:**
```json
{
  "materials": [
    {
      "matriell_id": 14,
      "antall": 5,
      "transf": false
    },
    {
      "matriell_id": 23,
      "antall": 2,
      "transf": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Processed 2 materials for job JOB-2025-001",
  "materials": [
    {
      "matriell_id": 14,
      "el_nr": "1000001",
      "tittel": "ÖLFLEX® Cable",
      "antall": 5,
      "transf": false,
      "action": "created"
    }
  ],
  "errors": [],
  "total_materials_in_job": 12
}
```

### Complete Job
```http
POST /jobber/{ordre_nr}/complete/
```

**Request Body:**
```json
{
  "notes": "Job completed successfully, all materials installed"
}
```

### Get Materials Summary
```http
GET /jobber/{ordre_nr}/materials_summary/
```

**Response:**
```json
{
  "jobb": {
    "ordre_nr": "JOB-2025-001",
    "tittel": "Electrical installation Oslo",
    "ferdig": false
  },
  "summary": {
    "total_material_types": 15,
    "total_items": 47,
    "categories": 3
  },
  "category_breakdown": {
    "Kabler og ledninger": {
      "count": 8,
      "items": 25
    },
    "Brytere og kontakter": {
      "count": 4,
      "items": 12
    }
  },
  "materials": [...]
}
```

---

## Job Materials (JobbMatriell)

### List Job Materials
```http
GET /jobbmatriell/
```

**Query Parameters:**
- `jobb`: Filter by job ordre_nr
- `matriell_el_nr`: Filter by material el_nr
- `transf`: Filter by transfer status
- `antall_min`: Minimum quantity
- `antall_max`: Maximum quantity

---

## Job Images

### List Images
```http
GET /jobb-images/
```

### Get Images by Job
```http
GET /jobb-images/by_job/?jobb_id=JOB-2025-001
```

**Response:**
```json
{
  "jobb": {
    "ordre_nr": "JOB-2025-001",
    "tittel": "Electrical installation Oslo"
  },
  "image_count": 5,
  "images": [
    {
      "id": 123,
      "name": "Installation progress",
      "image": "/media/job_images/img123.jpg",
      "jobb": "JOB-2025-001",
      "created_at": "2025-01-26T14:30:00+02:00"
    }
  ]
}
```

### Bulk Image Upload
```http
POST /jobb-images/bulk_upload/
```

**Request (multipart/form-data):**
- `jobb_id`: Job ordre_nr
- `images`: Array of image files
- `names`: Array of custom names (optional)

**Response:**
```json
{
  "message": "3 images uploaded successfully",
  "jobb_id": "JOB-2025-001",
  "uploaded": [
    {
      "id": 124,
      "name": "Cable installation",
      "filename": "IMG_001.jpg"
    }
  ],
  "errors": [],
  "total_images": 8
}
```

---

## Job Files

### List Files
```http
GET /jobb-files/
```

### Get Files by Job
```http
GET /jobb-files/by_job/?jobb_id=JOB-2025-001
```

### Bulk File Upload
```http
POST /jobb-files/bulk_upload/
```

**Request (multipart/form-data):**
- `jobb_id`: Job ordre_nr
- `files`: Array of files
- `names`: Array of custom names (optional)

### File Types Analysis
```http
GET /jobb-files/file_types/?jobb_id=JOB-2025-001
```

**Response:**
```json
{
  "summary": {
    "total_files": 12,
    "total_size_bytes": 15728640,
    "file_types_count": 4
  },
  "file_types": {
    "pdf": {
      "count": 5,
      "total_size": 8388608
    },
    "jpg": {
      "count": 4,
      "total_size": 4194304
    },
    "docx": {
      "count": 2,
      "total_size": 2097152
    },
    "xlsx": {
      "count": 1,
      "total_size": 1048576
    }
  },
  "jobb_id": "JOB-2025-001"
}
```

---

## Time Tracking (Timeliste)

### List Time Entries
```http
GET /timeliste/
```

**Query Parameters:**
- `user`: Filter by user ID
- `jobb`: Filter by job ordre_nr
- `dato_after`: Filter entries after date
- `dato_before`: Filter entries before date
- `this_month`: Filter current month (true/false)
- `this_week`: Filter current week (true/false)
- `timer_min`: Minimum hours
- `timer_max`: Maximum hours

**Example:**
```http
GET /timeliste/?jobb=JOB-2025-001&this_month=true
```

---

## Search & Filtering

### Global Search
Most endpoints support the `search` parameter for cross-field searching:

```http
GET /matriell/?search=nexans cable
GET /jobber/?search=oslo installation
GET /leverandorer/?search=nexans
```

### Advanced Filtering
All list endpoints support detailed filtering:

**Materials:**
```http
GET /matriell/?varemerke=NEXANS&approved=true&in_stock=true&kategori_blokknummer=10
```

**Jobs:**
```http
GET /jobber/?ferdig=false&created_after=2025-01-01&tittel__icontains=oslo
```

### Ordering
Use the `ordering` parameter to sort results:

```http
GET /matriell/?ordering=-created_at,el_nr
GET /jobber/?ordering=ferdig,-created_at
```

**Available ordering fields:**
- `created_at`, `updated_at`
- `el_nr`, `tittel`, `varemerke` (materials)
- `ordre_nr`, `tittel`, `date` (jobs)
- Use `-` prefix for descending order

---

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Detailed error message",
  "details": {
    "field_name": ["Field-specific error"]
  }
}
```

### Validation Errors
```json
{
  "el_nr": ["This field is required."],
  "leverandor": ["Leverandor 'UNKNOWN' not found"]
}
```

---

## Best Practices

### Performance Optimization
1. **Use Choice Endpoints**: For dropdowns, use `/choices/` endpoints instead of full list endpoints
2. **Limit Results**: Use `limit` parameter for choice endpoints (max: 500)
3. **Pagination**: Always handle pagination for list endpoints
4. **Specific Lookups**: Use lookup endpoints for single item retrieval
5. **Bulk Operations**: Use bulk endpoints for multiple item updates

### Frontend Integration Examples

#### React/JavaScript
```javascript
// Get materials with search and pagination
const getMateriels = async (page = 1, search = '', filters = {}) => {
  const params = new URLSearchParams({
    page,
    search,
    ...filters
  });

  const response = await fetch(`/app/memo/matriell/?${params}`, {
    headers: {
      'Authorization': `Token ${userToken}`,
      'Content-Type': 'application/json'
    }
  });

  return response.json();
};

// Get choices for dropdown
const getMaterialChoices = async (search = '') => {
  const response = await fetch(
    `/app/memo/matriell/choices/?search=${search}&limit=100`,
    {
      headers: { 'Authorization': `Token ${userToken}` }
    }
  );

  return response.json();
};

// Bulk update favorites
const bulkUpdateFavorites = async (elNrs, action) => {
  const response = await fetch('/app/memo/matriell/bulk_favorite/', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action, // 'add' or 'remove'
      el_nrs: elNrs
    })
  });

  return response.json();
};
```

### Error Handling
```javascript
const handleApiCall = async (apiCall) => {
  try {
    const response = await apiCall();

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'API call failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // Handle error in UI
    throw error;
  }
};
```

### Optimistic UI Updates
```javascript
// For favorites
const toggleFavorite = async (materialId, currentStatus) => {
  // Optimistic update
  setMaterialFavorite(materialId, !currentStatus);

  try {
    const action = !currentStatus ? 'POST' : 'DELETE';
    await fetch(`/app/memo/matriell/${materialId}/favorite/`, {
      method: action,
      headers: { 'Authorization': `Token ${userToken}` }
    });
  } catch (error) {
    // Revert on error
    setMaterialFavorite(materialId, currentStatus);
    throw error;
  }
};
```

---

## Support

For additional help or questions about the API:
- Check error messages for specific guidance
- Use the validation endpoints before submitting data
- Refer to the source code for detailed field requirements
- Contact the backend team for new feature requests

This API is designed to be frontend-friendly with comprehensive search, filtering, and bulk operations to handle large datasets efficiently.
