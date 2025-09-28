# Backend Development Requirements
## NXFS Frontend Integration Needs

**Document Version:** 1.0
**Date:** 2025-09-28
**Frontend Framework:** Next.js 15 with TypeScript
**API Integration:** Domain-driven architecture with Axios clients

---

## 🔥 High Priority - Missing API Endpoints

### 1. Blog Media API
**Status:** Missing
**Priority:** High
**Frontend Impact:** Blog admin functionality incomplete

#### Required Endpoints:
```
POST /api/blog/media/upload/
- File upload for blog images/attachments
- Support multipart/form-data
- Max file size: 10MB per file
- Supported formats: jpg, png, gif, webp, pdf, doc, docx

GET /api/blog/media/
- List all media files with pagination
- Filters: file_type, date_range, user_id
- Response: { count, results: MediaFile[] }

DELETE /api/blog/media/{id}/
- Delete media file and associated file storage
- Cascade delete from blog posts if referenced

GET /api/blog/media/{id}/
- Get media file details and metadata
```

#### Expected Response Format:
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

### 2. Advanced Task Filtering API
**Status:** Basic CRUD exists, advanced filtering missing
**Priority:** High
**Frontend Impact:** Limited task management functionality

#### Required Enhancements:
```
GET /api/tasks/?category=web&project=nxfs&status=in_progress&priority=high&due_date_start=2025-01-01&due_date_end=2025-12-31&search=bug
- Multiple category filtering
- Project-based filtering
- Date range filtering (due_date_start, due_date_end)
- Priority-based filtering
- Full-text search across title, description
- Combined filters with AND logic
```

#### Expected Response Format:
```typescript
interface TasksFilterResponse {
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

### 3. Bulk Operations API
**Status:** Missing
**Priority:** Medium
**Frontend Impact:** No batch operations available

#### Required Endpoints:
```
POST /api/tasks/bulk-update/
Request: {
  task_ids: number[];
  updates: {
    status?: 'todo' | 'in_progress' | 'completed';
    priority?: 'low' | 'medium' | 'high';
    category?: string[];
    project?: string;
  };
}
Response: {
  updated_count: number;
  failed_updates: { id: number; error: string }[];
}

DELETE /api/tasks/bulk-delete/
Request: { task_ids: number[] }
Response: { deleted_count: number; failed_deletes: number[] }
```

### 4. User Management API (Admin)
**Status:** Basic auth exists, admin management missing
**Priority:** Medium
**Frontend Impact:** No admin user management

#### Required Endpoints:
```
GET /api/admin/users/
- List all users with pagination
- Filters: is_active, role, registration_date

PUT /api/admin/users/{id}/
- Update user roles and permissions
- Enable/disable user accounts

POST /api/admin/users/{id}/reset-password/
- Admin-initiated password reset
```

---

## 🏗️ API Response Standardization

### 1. Error Response Format
**Status:** Inconsistent across endpoints
**Priority:** High
**Frontend Impact:** Error handling complexity

#### Required Standard Format:
```typescript
interface APIError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // User-friendly message
    details?: any;          // Additional error context
    field_errors?: {        // For validation errors
      [field: string]: string[];
    };
  };
  timestamp: string;
  request_id: string;       // For debugging
}
```

#### HTTP Status Code Standards:
- `400` - Validation errors, malformed requests
- `401` - Authentication required
- `403` - Permission denied
- `404` - Resource not found
- `409` - Conflict (duplicate data)
- `422` - Business logic validation failed
- `500` - Server error

### 2. Pagination Response Standardization
**Status:** Partially implemented
**Priority:** Medium
**Frontend Impact:** Inconsistent pagination handling

#### Current Django REST Framework Format (Keep):
```typescript
interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}
```

#### Ensure ALL list endpoints support:
- `page` and `page_size` query parameters
- Consistent metadata in response
- Maximum page_size limit (e.g., 100)

---

## 🔄 Real-time Features Enhancement

### 1. Socket.IO Backend Implementation
**Status:** Basic setup exists, business logic missing
**Priority:** Medium
**Frontend Impact:** Limited real-time functionality

#### Required Socket.IO Events:
```typescript
// Server -> Client Events
'task_updated': { task_id: number; task: Task; updated_by: number }
'task_created': { task: Task; created_by: number }
'task_deleted': { task_id: number; deleted_by: number }
'user_joined': { user_id: number; room: string }
'user_left': { user_id: number; room: string }
'notification': { type: string; message: string; data?: any }

// Client -> Server Events
'join_room': { room: string }      // e.g., 'project_123', 'tasks'
'leave_room': { room: string }
'task_update': { task_id: number; updates: Partial<Task> }
```

#### Room Management:
- `tasks` - Global task updates
- `project_{id}` - Project-specific updates
- `user_{id}` - User-specific notifications

### 2. User Presence Tracking
**Status:** Missing
**Priority:** Low
**Frontend Impact:** No collaborative indicators

#### Required Implementation:
- Track online users per room/project
- Emit presence updates on join/leave
- Cleanup inactive connections
- Store last_seen timestamps

---

## 📊 System Monitoring Improvements

### 1. System Stats Data Consistency
**Status:** Fixed in frontend, verify backend
**Priority:** Low
**Context:** Frontend now handles missing `cpu_percent` gracefully

#### Recommendations:
- Ensure all SystemStats fields are populated consistently
- Add data validation before saving stats
- Handle hardware detection failures gracefully
- Add logging for failed stat collection

### 2. Historical Data Cleanup
**Status:** Unknown
**Priority:** Low

#### Suggested Features:
- Automatic cleanup of old system stats (>30 days)
- Data aggregation for long-term storage
- Performance optimization for large datasets

---

## 🔐 Security & Performance Requirements

### 1. Authentication Enhancements
**Status:** JWT working, needs improvements
**Priority:** Medium

#### Required Features:
- Token refresh mechanism (automatic)
- Session timeout configuration
- Rate limiting per user/endpoint
- Audit logging for sensitive operations

### 2. API Performance
**Status:** Good for small datasets
**Priority:** Medium

#### Optimization Needs:
- Database query optimization for large datasets
- Response caching for frequently accessed data
- Async processing for heavy operations
- API response compression

---

## 🌐 Integration Context

### Frontend API Client Structure
The frontend uses a domain-driven API architecture:

```
src/lib/api/
├── auth/           # Authentication & user management
├── blog/           # Blog posts and media
├── chat/           # N8N chatbot integration
├── memo/           # Electrical memo system
├── system/         # System monitoring & stats
├── tasks/          # Task management
├── shared/         # Common utilities & types
└── index.ts        # Centralized exports
```

### Current Authentication Flow
- JWT tokens stored in Zustand store
- Automatic token refresh via Axios interceptors
- Global error handling with toast notifications
- Authentication check on all protected routes

### Error Handling Expectations
The frontend expects:
- Consistent error response format
- Proper HTTP status codes
- Toast-friendly error messages
- Field-level validation errors for forms

### TypeScript Integration
- All API responses must match TypeScript interfaces
- Domain-specific type definitions in each API module
- Support for both direct arrays and paginated responses
- Null safety for optional fields

---

## 📋 Implementation Priority

### Phase 1 (Week 2) - Critical Missing APIs
1. Blog Media API endpoints
2. Advanced Task Filtering
3. Error response standardization

### Phase 2 (Week 3) - Bulk Operations & Admin
1. Bulk task operations
2. Admin user management API
3. Performance optimizations

### Phase 3 (Week 4) - Real-time Features
1. Socket.IO business logic implementation
2. User presence tracking
3. Live notification system

### Phase 4 (Week 5+) - Enhancements
1. Advanced security features
2. Analytics and reporting APIs
3. Performance monitoring

---

## 🧪 Testing Requirements

### API Testing Expectations
- Unit tests for all new endpoints
- Integration tests for complex workflows
- Performance testing for bulk operations
- Error handling validation

### Frontend Integration Testing
- Automated API contract testing
- Frontend E2E tests depend on stable API
- Consistent test data fixtures needed

---

## 📞 Communication & Handoff

### Questions for Backend Team
1. **Timeline**: What's the estimated timeline for Phase 1 items?
2. **Bulk Operations**: Any concerns about performance for large datasets?
3. **Real-time**: Current Socket.IO infrastructure capacity?
4. **Testing**: Preferred testing frameworks and patterns?

### Frontend Team Contact
- **Primary Contact**: [Your Name]
- **Technical Questions**: Available for API integration discussions
- **Testing**: Can provide frontend integration testing support

### Documentation Updates Needed
- Update API schema at `api.nxfs.no/schema/` after implementation
- Provide example requests/responses for new endpoints
- Document any breaking changes with migration guide

---

**Next Steps:**
1. Backend team review and estimate effort
2. Prioritize items based on business needs
3. Plan implementation sprints
4. Set up regular sync meetings for integration testing

*Generated from Frontend TODO.md analysis - 2025-09-28*
