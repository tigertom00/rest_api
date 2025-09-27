# Matriell Favorites API Documentation

## Overview
The Favorites API provides comprehensive endpoints for managing favorite Matriell items. This API supports individual item favorites, bulk operations, and listing favorites with pagination.

## Base URL
```
https://api.nxfs.no/app/memo/matriell/
```

## Authentication
All endpoints require authentication. Include the authorization header:
```
Authorization: Token <your-api-token>
```

## Endpoints

### 1. Individual Item Favorite Management

#### Check Favorite Status
```http
GET /app/memo/matriell/{id}/favorite/
```

**Response (200 OK):**
```json
{
  "el_nr": "1000001",
  "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5",
  "favorites": false
}
```

#### Add to Favorites
```http
POST /app/memo/matriell/{id}/favorite/
```

**Response (201 Created):**
```json
{
  "message": "Item added to favorites",
  "favorites": true
}
```

**Response if already favorited (200 OK):**
```json
{
  "message": "Item is already in favorites",
  "favorites": true
}
```

#### Remove from Favorites
```http
DELETE /app/memo/matriell/{id}/favorite/
```

**Response (204 No Content):**
- Empty response body

**Response if not in favorites (200 OK):**
```json
{
  "message": "Item is not in favorites",
  "favorites": false
}
```

### 2. List All Favorites

#### Get Favorites List
```http
GET /app/memo/matriell/favorites/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 200)

**Response (200 OK):**
```json
{
  "pagination": {
    "count": 150,
    "total_pages": 3,
    "current_page": 1,
    "page_size": 50,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  },
  "links": {
    "next": "https://api.nxfs.no/app/memo/matriell/favorites/?page=2",
    "previous": null
  },
  "results": [
    {
      "id": 14,
      "el_nr": "1000001",
      "tittel": "ÖLFLEX® 2YSLCYK-JB 3X2,5+3G0,5",
      "varemerke": "LAPP KABEL",
      "varenummer": "0012504",
      "leverandor_name": "LAPP KABEL AS",
      "kategori_name": "Kabler og ledninger",
      "approved": true,
      "in_stock": true,
      "favorites": true,
      "created_at": "2025-09-26T10:30:00+02:00"
    }
  ]
}
```

### 3. Bulk Operations

#### Bulk Add/Remove Favorites
```http
POST /app/memo/matriell/bulk_favorite/
```

**Request Body:**
```json
{
  "action": "add",
  "el_nrs": ["1000001", "1000002", "1000003"]
}
```

**Request Body (Remove):**
```json
{
  "action": "remove",
  "el_nrs": ["1000001", "1000002"]
}
```

**Response (200 OK):**
```json
{
  "message": "3 items added to favorites",
  "updated_count": 3,
  "action": "add"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Action must be 'add' or 'remove'"
}
```

```json
{
  "error": "el_nrs list cannot be empty"
}
```

## Frontend Integration Examples

### JavaScript/Fetch API

#### Add to Favorites
```javascript
async function addToFavorites(itemId) {
  const response = await fetch(`/app/memo/matriell/${itemId}/favorite/`, {
    method: 'POST',
    headers: {
      'Authorization': `Token ${userToken}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.ok) {
    const data = await response.json();
    console.log('Added to favorites:', data.message);
    return true;
  }
  return false;
}
```

#### Remove from Favorites
```javascript
async function removeFromFavorites(itemId) {
  const response = await fetch(`/app/memo/matriell/${itemId}/favorite/`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Token ${userToken}`
    }
  });

  return response.ok;
}
```

#### Get Favorites List
```javascript
async function getFavorites(page = 1, pageSize = 50) {
  const response = await fetch(
    `/app/memo/matriell/favorites/?page=${page}&page_size=${pageSize}`,
    {
      headers: {
        'Authorization': `Token ${userToken}`
      }
    }
  );

  if (response.ok) {
    return await response.json();
  }
  throw new Error('Failed to fetch favorites');
}
```

#### Bulk Operations
```javascript
async function bulkFavorites(action, elNumbers) {
  const response = await fetch('/app/memo/matriell/bulk_favorite/', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${userToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: action, // 'add' or 'remove'
      el_nrs: elNumbers
    })
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`${data.updated_count} items ${action === 'add' ? 'added to' : 'removed from'} favorites`);
    return data;
  }
  throw new Error('Bulk operation failed');
}
```

## Status Codes

- **200 OK**: Successful operation
- **201 Created**: Item successfully added to favorites
- **204 No Content**: Item successfully removed from favorites
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Item not found

## Best Practices

1. **Optimistic UI Updates**: Update UI immediately, then sync with server
2. **Error Handling**: Always handle network errors and API failures gracefully
3. **Pagination**: Use appropriate page sizes for favorites list
4. **Bulk Operations**: For multiple items, use bulk endpoints for better performance
5. **Status Checking**: Use GET endpoint to verify current favorite status when needed

## Performance Notes

- Favorites list uses optimized serializer for faster loading
- Database queries are optimized with select_related for foreign keys
- Pagination prevents memory issues with large favorite lists
- Bulk operations are atomic and use efficient database updates
