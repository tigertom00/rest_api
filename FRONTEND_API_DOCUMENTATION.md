# Frontend API Integration Guide

**Generated:** 2025-09-28
**Status:** All Phase 1-4 Requirements Complete
**API Version:** 1.0

---

## 🎉 Implementation Complete

All backend API requirements from `BACKEND_REQUIREMENTS.md` have been successfully implemented and are ready for frontend integration. This document provides comprehensive guidance for the frontend team.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [New API Endpoints](#new-api-endpoints)
3. [Enhanced Endpoints](#enhanced-endpoints)
4. [Authentication & Security](#authentication--security)
5. [Error Handling](#error-handling)
6. [Real-time Features](#real-time-features)
7. [Performance Monitoring](#performance-monitoring)
8. [TypeScript Interfaces](#typescript-interfaces)
9. [Integration Examples](#integration-examples)
10. [Testing & Debugging](#testing--debugging)

---

## 🚀 Quick Start

### Base URL

```
Production: https://api.nxfs.no
Development: http://localhost:8000
```

### Authentication

All API endpoints require authentication using one of:

- **JWT Bearer Token**: `Authorization: Bearer <token>`
- **OAuth2**: For external integrations
- **Clerk Authentication**: For user management

### Response Format

All responses include performance headers:

```
X-Response-Time: 0.125s
X-DB-Queries: 3
```

---

## 🆕 New API Endpoints

### 1. Blog Media Management

#### Upload Media File

```http
POST /app/blog/media/
Content-Type: multipart/form-data

{
  "file": <file>,
  "description": "Optional description"
}
```

**Response:**

```typescript
interface MediaFile {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  uploaded_by: number;
  url: string;
  thumbnail_url?: string;
}
```

#### List Media Files

```http
GET /app/blog/media/
```

**Query Parameters:**

- `file_type`: Filter by file type (image, document, etc.)
- `date_start`: Start date filter (ISO format)
- `date_end`: End date filter (ISO format)
- `page`: Page number
- `page_size`: Items per page (max 100)

#### Get/Delete Media File

```http
GET /app/blog/media/{id}/
DELETE /app/blog/media/{id}/
```

### 2. Bulk Task Operations

#### Bulk Update Tasks

```http
POST /app/tasks/tasks/bulk-update/
Content-Type: application/json

{
  "task_ids": [1, 2, 3],
  "updates": {
    "status": "completed",
    "priority": "high",
    "category": ["web", "design"],
    "project": "nxfs"
  }
}
```

**Response:**

```typescript
interface BulkUpdateResponse {
  updated_count: number;
  failed_updates: Array<{
    id: number;
    error: string;
  }>;
}
```

#### Bulk Delete Tasks

```http
DELETE /app/tasks/tasks/bulk-delete/
Content-Type: application/json

{
  "task_ids": [1, 2, 3]
}
```

**Response:**

```typescript
interface BulkDeleteResponse {
  deleted_count: number;
  failed_deletes: number[];
}
```

### 3. Admin User Management

#### List Users (Admin Only)

```http
GET /api/admin/users/
```

**Query Parameters:**

- `is_active`: Filter by active status
- `is_staff`: Filter by staff status
- `registration_date_start`: Registration date filter
- `registration_date_end`: Registration date filter
- `search`: Search by email, username, name

#### Reset User Password (Admin Only)

```http
POST /api/admin/users/{id}/reset-password/
Content-Type: application/json

{
  "new_password": "new_secure_password123"
}
```

#### Toggle User Active Status (Admin Only)

```http
PATCH /api/admin/users/{id}/toggle-active/
Content-Type: application/json

{
  "is_active": true
}
```

### 4. Performance Monitoring

#### Health Check (Public)

```http
GET /api/health/
```

**Response:**

```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database: string;
    cache: string;
    cpu: string;
    memory: string;
    disk: string;
  };
}
```

#### Performance Metrics (Admin Only)

```http
GET /api/admin/metrics/
```

**Response:**

```typescript
interface PerformanceMetrics {
  system: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  };
  database: {
    vendor: string;
    connections?: number;
    query_cache_hit_rate?: number;
  };
  cache: {
    cache_working: boolean;
    hit_rate?: number;
  };
  api_summary: {
    total_requests: number;
    avg_response_time: number;
    max_response_time: number;
    slow_requests: number;
  };
}
```

---

## 🔧 Enhanced Endpoints

### Advanced Task Filtering

The `/app/tasks/tasks/` endpoint now supports advanced filtering:

```http
GET /app/tasks/tasks/?category=web&category=design&project=nxfs&status=in_progress&priority=high&due_date_start=2025-01-01&due_date_end=2025-12-31&search=bug
```

**New Query Parameters:**

- `category`: Multiple categories (AND logic)
- `project`: Filter by project name
- `status`: Multiple statuses
- `priority`: Multiple priorities
- `due_date_start`: Start date filter
- `due_date_end`: End date filter
- `search`: Full-text search across title, description, notes

**Enhanced Response:**

```typescript
interface TasksResponse {
  count: number;
  next?: string;
  previous?: string;
  results: Task[];
  filters_applied: {
    categories?: string[];
    projects?: string[];
    status?: string[];
    priority?: string[];
    date_range?: { start: string; end: string };
    search?: string;
  };
}
```

---

## 🔐 Authentication & Security

### Rate Limiting

Different rate limits apply based on operation type:

- **API Requests**: 1000/hour per user
- **Anonymous**: 100/hour per IP
- **File Uploads**: 50/hour per user
- **Bulk Operations**: 10/hour per user
- **Admin Operations**: 200/hour per user
- **Login Attempts**: 5/minute per IP

### Headers to Include

```typescript
const headers = {
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
  'User-Agent': 'YourApp/1.0',
};
```

---

## ⚠️ Error Handling

### Standardized Error Format

All endpoints now return consistent error responses:

```typescript
interface APIError {
  error: {
    code: string; // Machine-readable error code
    message: string; // User-friendly message
    details?: any; // Additional error context
    field_errors?: {
      // For validation errors
      [field: string]: string[];
    };
  };
  timestamp: string;
  request_id: string; // For debugging
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: Missing or invalid authentication
- `PERMISSION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `INTERNAL_SERVER_ERROR`: Server error

### Axios Error Handling Example

```typescript
import axios from 'axios';

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      const apiError = error.response.data as APIError;
      console.error(
        `API Error [${apiError.error.code}]:`,
        apiError.error.message
      );
      console.error('Request ID:', apiError.request_id);

      // Handle specific error codes
      switch (apiError.error.code) {
        case 'AUTHENTICATION_REQUIRED':
          // Redirect to login
          break;
        case 'RATE_LIMIT_EXCEEDED':
          // Show rate limit message
          break;
        case 'VALIDATION_ERROR':
          // Display field errors
          if (apiError.error.field_errors) {
            Object.entries(apiError.error.field_errors).forEach(
              ([field, errors]) => {
                console.error(`${field}: ${errors.join(', ')}`);
              }
            );
          }
          break;
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 🔄 Real-time Features

### WebSocket Connection

Connect to real-time task updates:

```typescript
const ws = new WebSocket('wss://api.nxfs.no/ws/tasks/');

ws.onopen = () => {
  console.log('Connected to real-time updates');

  // Join specific rooms
  ws.send(
    JSON.stringify({
      type: 'join_room',
      room: 'task_tasks', // Global tasks room
    })
  );

  ws.send(
    JSON.stringify({
      type: 'join_room',
      room: `task_user_${userId}`, // User-specific room
    })
  );

  ws.send(
    JSON.stringify({
      type: 'join_room',
      room: `task_project_${projectId}`, // Project-specific room
    })
  );
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'task_created':
      handleTaskCreated(data.task);
      break;
    case 'task_updated':
      handleTaskUpdated(data.task_id, data.task);
      break;
    case 'task_deleted':
      handleTaskDeleted(data.task_id);
      break;
  }
};
```

### Available Events

**Server → Client:**

- `task_created`: New task created
- `task_updated`: Task modified
- `task_deleted`: Task removed
- `user_joined`: User joined room
- `user_left`: User left room

**Client → Server:**

- `join_room`: Join a specific room
- `leave_room`: Leave a room

---

## 📊 Performance Monitoring

### Response Headers

Every API response includes performance metrics:

```typescript
interface ResponseHeaders {
  'X-Response-Time': string; // e.g., "0.125s"
  'X-DB-Queries': string; // e.g., "3"
}
```

### Monitoring Integration

Use these headers for client-side performance monitoring:

```typescript
axios.interceptors.response.use((response) => {
  const responseTime = response.headers['x-response-time'];
  const dbQueries = response.headers['x-db-queries'];

  // Log slow requests
  if (parseFloat(responseTime) > 1.0) {
    console.warn(`Slow request: ${response.config.url} took ${responseTime}`);
  }

  // Log heavy database usage
  if (parseInt(dbQueries) > 10) {
    console.warn(
      `Heavy DB usage: ${response.config.url} made ${dbQueries} queries`
    );
  }

  return response;
});
```

---

## 🏷️ TypeScript Interfaces

### Core Interfaces

```typescript
interface Task {
  id: number;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  project?: Project;
  category: Category[];
  user_id: number;
  created_at: string;
  updated_at: string;
  notes?: string;
  images: TaskImage[];
}

interface Project {
  id: number;
  name: string;
  user_id: number;
  tasks: number[];
  images: ProjectImage[];
  created_at: string;
  updated_at: string;
}

interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
}

interface MediaFile {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  uploaded_by: number;
  url: string;
  thumbnail_url?: string;
}

interface User {
  id: number;
  email: string;
  username: string;
  display_name: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login?: string;
}

interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}
```

---

## 💡 Integration Examples

### Axios Configuration

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors as shown in Error Handling section
    return Promise.reject(error);
  }
);
```

### React Hook for Tasks

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from './api';

interface UseTasksOptions {
  category?: string[];
  project?: string;
  status?: string[];
  search?: string;
}

export function useTasks(options: UseTasksOptions = {}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();

        options.category?.forEach((cat) => params.append('category', cat));
        if (options.project) params.append('project', options.project);
        options.status?.forEach((status) => params.append('status', status));
        if (options.search) params.append('search', options.search);

        const response = await apiClient.get(`/app/tasks/tasks/?${params}`);
        setTasks(response.data.results);
        setError(null);
      } catch (err) {
        setError('Failed to fetch tasks');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [options.category, options.project, options.status, options.search]);

  return { tasks, loading, error };
}
```

### Bulk Operations

```typescript
export async function bulkUpdateTasks(
  taskIds: number[],
  updates: Partial<Task>
): Promise<BulkUpdateResponse> {
  const response = await apiClient.post('/app/tasks/tasks/bulk-update/', {
    task_ids: taskIds,
    updates,
  });
  return response.data;
}

export async function bulkDeleteTasks(
  taskIds: number[]
): Promise<BulkDeleteResponse> {
  const response = await apiClient.delete('/app/tasks/tasks/bulk-delete/', {
    data: { task_ids: taskIds },
  });
  return response.data;
}
```

### File Upload

```typescript
export async function uploadMediaFile(
  file: File,
  description?: string
): Promise<MediaFile> {
  const formData = new FormData();
  formData.append('file', file);
  if (description) {
    formData.append('description', description);
  }

  const response = await apiClient.post('/app/blog/media/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}
```

---

## 🧪 Testing & Debugging

### Health Check Integration

```typescript
export async function checkAPIHealth(): Promise<HealthStatus> {
  const response = await axios.get('/api/health/');
  return response.data;
}

// Use in app initialization
useEffect(() => {
  checkAPIHealth()
    .then((health) => {
      if (health.status !== 'healthy') {
        console.warn('API is degraded:', health.checks);
      }
    })
    .catch((error) => {
      console.error('API is unavailable:', error);
    });
}, []);
```

### Performance Monitoring

```typescript
// Track API performance
function trackAPIPerformance(
  url: string,
  responseTime: string,
  dbQueries: string
) {
  // Send to your analytics service
  analytics.track('api_request', {
    url,
    response_time: parseFloat(responseTime),
    db_queries: parseInt(dbQueries),
    timestamp: new Date().toISOString(),
  });
}
```

### Debug Headers

Include request ID in error reports:

```typescript
const handleAPIError = (error: any, context: string) => {
  const requestId = error.response?.data?.request_id;

  errorReporting.captureException(error, {
    extra: {
      context,
      request_id: requestId,
      url: error.config?.url,
      method: error.config?.method,
    },
  });
};
```

---

## 🚦 Rate Limiting & Best Practices

### Handling Rate Limits

```typescript
const handleRateLimit = (error: any) => {
  if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'];
    if (retryAfter) {
      setTimeout(() => {
        // Retry the request
      }, parseInt(retryAfter) * 1000);
    }
  }
};
```

### Optimizing Bulk Operations

```typescript
// Process in batches to avoid rate limits
async function processBulkUpdates(updates: Array<{ id: number; data: any }>) {
  const batchSize = 50; // Within rate limit

  for (let i = 0; i < updates.length; i += batchSize) {
    const batch = updates.slice(i, i + batchSize);
    await bulkUpdateTasks(
      batch.map((u) => u.id),
      batch[0].data // Assuming same updates for all
    );

    // Add delay between batches if needed
    if (i + batchSize < updates.length) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
}
```

---

## 📝 Migration Notes

### Breaking Changes

- None! All existing endpoints remain unchanged
- New endpoints are additive only

### Recommended Updates

1. **Update error handling** to use new standardized format
2. **Add performance monitoring** using response headers
3. **Implement real-time updates** for better UX
4. **Use bulk operations** for better performance
5. **Add health checks** for better reliability

---

## 🎯 Next Steps for Frontend

1. **Update API client** with new endpoints and interfaces
2. **Implement error handling** using standardized format
3. **Add WebSocket integration** for real-time features
4. **Update task management** to use advanced filtering
5. **Implement bulk operations** in UI
6. **Add file upload** functionality for blog media
7. **Set up performance monitoring** dashboard
8. **Add health status** indicator in app

---

## 📞 Support & Resources

- **API Schema**: `https://api.nxfs.no/schema/`
- **Swagger UI**: `https://api.nxfs.no/schema/swagger-ui/`
- **Health Check**: `https://api.nxfs.no/api/health/`
- **Performance Metrics**: `https://api.nxfs.no/api/admin/metrics/` (Admin only)

---

**🎉 Happy Coding!**

_All features are production-ready and thoroughly tested. The API is optimized for performance with comprehensive error handling, rate limiting, and real-time capabilities._

---

_Generated: 2025-09-28_
_Backend Team Implementation Complete_
