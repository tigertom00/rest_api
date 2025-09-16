# Django REST API Documentation

## Overview

This Django REST API provides comprehensive backend services for a web application with JWT authentication, user management, task management, blog functionality, memo systems, and LLM provider integrations. The API uses Django REST Framework with JWT authentication via Simple JWT and Clerk integration.

## Base URL

- **Development**: `http://127.0.0.1:8000/` or `http://localhost:8000/`
- **Production**: `https://api.nxfs.no/`

## Authentication

The API supports multiple authentication methods to accommodate different use cases:

### JWT Authentication

The API uses JSON Web Tokens (JWT) for authentication with the following configuration:

- **Access Token Lifetime**: 1 minute
- **Refresh Token Lifetime**: 14 days
- **Token Rotation**: Enabled (new refresh token issued on refresh)
- **Blacklist After Rotation**: Enabled
- **Header Format**: `Authorization: Bearer <token>`

### Authentication Endpoints

#### 1. Obtain Token Pair
```
POST /token/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 2. Refresh Token
```
POST /token/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 3. Blacklist Token (Logout)
```
POST /token/blacklist/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### DRF Token Authentication

For simpler integrations (n8n, OpenWebUI, etc.), the API supports Django REST Framework Token Authentication:

#### Generate API Token
```bash
# Create a token for a user
python manage.py shell -c "
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()
user = User.objects.get(email='your@email.com')
token, created = Token.objects.get_or_create(user=user)
print(f'Token: {token.key}')
"
```

#### Usage
```
Authorization: Token YOUR_API_TOKEN_HERE
```

### Clerk Integration

The API also supports Clerk authentication:
- **Clerk Webhook**: `POST /clerk/webhook/`
- Custom authentication class: `ClerkAuthentication`

---

## User Management

### User Model (`CustomUser`)

**Fields:**
```typescript
interface User {
    id: number;
    username?: string;
    email: string; // unique, used as USERNAME_FIELD
    display_name?: string;
    date_of_birth?: string; // ISO date
    address?: string;
    city?: string;
    country?: string;
    website?: string; // URL
    phone?: string; // unique
    profile_picture: string; // ImageField URL
    clerk_profile_image_url?: string;
    dark_mode: boolean;
    clerk_user_id?: string;
    has_image: boolean;
    two_factor_enabled: boolean;
    clerk_updated_at: string; // ISO datetime
    chat_session_id?: string; // UUID
    language: 'en' | 'no';
    date_joined: string; // ISO datetime
    last_login?: string; // ISO datetime
    is_active: boolean;
    is_staff: boolean;
    is_superuser: boolean;
}
```

**Related Models:**
- `UserEmail`: Additional email addresses
- `UserPhone`: Additional phone numbers

### User Endpoints

#### 1. User Registration
```
POST /register/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "secure_password",
    "username": "optional_username",
    "display_name": "Optional Display Name"
}
```

#### 2. User List/Details (ViewSet)
```
GET /user/          # List all users (admin only)
GET /user/{id}/     # Get specific user details
PUT /user/{id}/     # Update user
PATCH /user/{id}/   # Partial update user
DELETE /user/{id}/  # Delete user
```

---

## Task Management

### Task Model

**Fields:**
```typescript
interface Task {
    id: number;
    title: string;
    title_nb?: string; // Norwegian translation
    description?: string;
    description_nb?: string;
    notes?: string;
    status: 'todo' | 'in_progress' | 'completed';
    status_nb: 'å gjøre' | 'pågående' | 'fullført';
    priority: 'low' | 'medium' | 'high';
    due_date?: string; // ISO date
    estimated_time?: number; // decimal hours
    completed: boolean;
    completed_at?: string; // ISO datetime
    user_id: number; // Foreign key to User
    created_at: string; // ISO datetime
    updated_at: string; // ISO datetime
    category: number[]; // Array of Category IDs (ManyToMany)
    project?: number; // Foreign key to Project (optional)
}
```

### Category Model

**Fields:**
```typescript
interface Category {
    id: number;
    slug: string; // unique
    name: string;
    name_nb?: string;
}
```

### Project Model

**Fields:**
```typescript
interface Project {
    id: number;
    name: string;
    name_nb?: string;
    description?: string;
    description_nb?: string;
    user_id: number;
    created_at: string;
    updated_at: string;
    completed: boolean;
    completed_at?: string;
    tasks: number[]; // Array of Task IDs
    status: 'todo' | 'in_progress' | 'completed';
    status_nb: 'å gjøre' | 'pågående' | 'fullført';
}
```

### Task Endpoints

#### 1. Tasks (ViewSet)
```
GET /app/tasks/                 # List all tasks
POST /app/tasks/               # Create new task
GET /app/tasks/{id}/           # Get specific task
PUT /app/tasks/{id}/           # Update task
PATCH /app/tasks/{id}/         # Partial update task
DELETE /app/tasks/{id}/        # Delete task
```

#### 2. Categories (ViewSet)
```
GET /app/tasks/categories/             # List all categories
POST /app/tasks/categories/           # Create new category
GET /app/tasks/categories/{id}/       # Get specific category
PUT /app/tasks/categories/{id}/       # Update category
PATCH /app/tasks/categories/{id}/     # Partial update category
DELETE /app/tasks/categories/{id}/    # Delete category
```

#### 3. Projects (ViewSet)
```
GET /app/tasks/projects/              # List all projects
POST /app/tasks/projects/            # Create new project
GET /app/tasks/projects/{id}/        # Get specific project
PUT /app/tasks/projects/{id}/        # Update project
PATCH /app/tasks/projects/{id}/      # Partial update project
DELETE /app/tasks/projects/{id}/     # Delete project
```

**Example Task Creation:**
```json
{
    "title": "Complete API documentation",
    "description": "Write comprehensive API documentation for frontend integration",
    "status": "todo",
    "priority": "high",
    "due_date": "2024-12-31",
    "estimated_time": 4.5,
    "category": [1, 2],
    "project": 3
}
```

---

## Blog Management

### BlogPost Model

**Fields:**
```typescript
interface BlogPost {
    id: number;
    author: number; // Foreign key to User
    title: string;
    title_nb?: string;
    slug: string; // auto-generated, unique with author
    excerpt?: string;
    excerpt_nb?: string;
    tags: number[]; // Array of Tag IDs
    body_markdown: string;
    body_markdown_nb?: string;
    status: 'draft' | 'published';
    meta_title?: string;
    meta_description?: string;
    published_at?: string; // ISO datetime
    created_at: string;
    updated_at: string;
    body_html?: string; // computed property from markdown
}
```

### Tag Model

**Fields:**
```typescript
interface Tag {
    id: number;
    name: string; // unique
    slug: string; // auto-generated
}
```

### PostImage Model

**Fields:**
```typescript
interface PostImage {
    id: number;
    post: number; // Foreign key to BlogPost
    image: string; // ImageField URL
    alt_text?: string;
    caption?: string;
    order: number;
}
```

### PostAudio Model

**Fields:**
```typescript
interface PostAudio {
    id: number;
    post: number;
    audio: string; // FileField URL
    title?: string;
    duration_seconds?: number;
    order: number;
}
```

### PostYouTube Model

**Fields:**
```typescript
interface PostYouTube {
    id: number;
    post: number;
    url: string; // YouTube URL
    video_id: string; // Extracted video ID
    title?: string;
    order: number;
}
```

### Blog Endpoints

#### 1. Blog Posts (ViewSet)
```
GET /api/posts/                # List all posts
POST /api/posts/              # Create new post
GET /api/posts/{id}/          # Get specific post
PUT /api/posts/{id}/          # Update post
PATCH /api/posts/{id}/        # Partial update post
DELETE /api/posts/{id}/       # Delete post
```

#### 2. Post Images (Nested ViewSet)
```
GET /api/posts/{post_id}/images/           # List images for post
POST /api/posts/{post_id}/images/         # Add image to post
GET /api/posts/{post_id}/images/{id}/     # Get specific image
PUT /api/posts/{post_id}/images/{id}/     # Update image
DELETE /api/posts/{post_id}/images/{id}/  # Delete image
```

#### 3. Post Audio (Nested ViewSet)
```
GET /api/posts/{post_id}/audio/           # List audio files for post
POST /api/posts/{post_id}/audio/         # Add audio to post
GET /api/posts/{post_id}/audio/{id}/     # Get specific audio
PUT /api/posts/{post_id}/audio/{id}/     # Update audio
DELETE /api/posts/{post_id}/audio/{id}/  # Delete audio
```

**Example Blog Post Creation:**
```json
{
    "title": "Getting Started with Django REST API",
    "excerpt": "Learn how to build a RESTful API with Django",
    "body_markdown": "# Introduction\n\nThis is a guide to building APIs...",
    "status": "draft",
    "tags": [1, 2, 3],
    "meta_title": "Django REST API Tutorial",
    "meta_description": "Complete guide to Django REST Framework"
}
```

---

## LLM Providers Management

### Llmproviders Model

**Fields:**
```typescript
interface LlmProvider {
    id: number;
    name?: string;
    url?: string; // URL field
    created_at: string;
    updated_at: string;
    description?: string;
    description_nb?: string;
    strengths_en: string[]; // JSON array
    strengths_no: string[]; // JSON array
    pricing: 'Free' | 'Paid';
    pricing_nb: 'Gratis' | 'Betalt';
    icon?: string; // ImageField URL
    tags: number[]; // Array of Tag IDs
}
```

### Tag Model (Components)

**Fields:**
```typescript
interface ComponentTag {
    id: number;
    name_en: string;
    name_no?: string;
}
```

### LLM Provider Endpoints

#### 1. LLM Providers (ViewSet)
```
GET /app/providers/               # List all providers
POST /app/providers/             # Create new provider
GET /app/providers/{id}/         # Get specific provider
PUT /app/providers/{id}/         # Update provider
PATCH /app/providers/{id}/       # Partial update provider
DELETE /app/providers/{id}/      # Delete provider
```

#### 2. Provider Tags (ViewSet)
```
GET /app/providers/tags/         # List all tags
POST /app/providers/tags/       # Create new tag
GET /app/providers/tags/{id}/   # Get specific tag
PUT /app/providers/tags/{id}/   # Update tag
DELETE /app/providers/tags/{id}/ # Delete tag
```

**Example LLM Provider Creation:**
```json
{
    "name": "OpenAI GPT-4",
    "url": "https://openai.com/gpt-4",
    "description": "Advanced language model for various tasks",
    "strengths_en": ["reasoning", "coding", "creative writing"],
    "pricing": "Paid",
    "tags": [1, 2]
}
```

---

## MCP Server (Model Context Protocol)

The API includes a Model Context Protocol (MCP) server that enables AI agents and tools (like n8n, OpenWebUI, Claude Desktop) to interact with your Django data using natural language queries.

### MCP Server Endpoints

```
GET/POST /mcp/          # MCP protocol endpoint
```

### Authentication

The MCP server uses DRF Token Authentication:

```
Authorization: Token YOUR_API_TOKEN_HERE
```

### Available MCP Tools

The MCP server automatically exposes all your Django models as queryable tools:

#### Task Management Tools
- **TasksToolset**: Query and manage tasks
- **ProjectsToolset**: Query and manage projects
- **CategoriesToolset**: Query and manage task categories

#### Content Management Tools
- **BlogPostToolset**: Query and manage blog posts
- **BlogTagToolset**: Query and manage blog tags
- **SiteSettingsToolset**: Query site settings

#### Business Tools
- **LeverandorerToolset**: Query suppliers (leverandører)
- **MatriellToolset**: Query materials (matriell)
- **JobberToolset**: Query jobs (jobber)
- **JobbMatriellToolset**: Query job materials
- **TimelisteToolset**: Query time tracking entries

#### Component Tools
- **TodoToolset**: Query todo items
- **ComponentTagToolset**: Query component tags
- **LlmprovidersToolset**: Query LLM providers

### MCP Tool Usage Examples

#### Natural Language Queries
```json
{
  "tool": "TasksToolset",
  "request": "Find all high priority tasks that are not completed",
  "context": "I need to see urgent work items"
}
```

#### Advanced Queries
```json
{
  "tool": "query_data_collections",
  "collection": "task",
  "search_pipeline": [
    {"$match": {"status": "todo", "priority": "high"}},
    {"$sort": {"due_date": 1}},
    {"$limit": 10}
  ]
}
```

### MongoDB-Style Aggregation

The MCP server supports MongoDB aggregation pipeline syntax for complex queries:

**Supported Stages:**
- `$lookup` - Join collections
- `$match` - Filter documents
- `$sort` - Sort results
- `$limit` - Limit results
- `$project` - Select fields
- `$search` - Full-text search
- `$group` - Group and aggregate

**Example - Tasks with Project Information:**
```json
{
  "collection": "task",
  "search_pipeline": [
    {
      "$lookup": {
        "from": "project",
        "localField": "project",
        "foreignField": "_id",
        "as": "project_info"
      }
    },
    {
      "$match": {
        "status": "in_progress",
        "project_info.status": "active"
      }
    },
    {
      "$project": {
        "title": 1,
        "status": 1,
        "project_name": "$project_info.name"
      }
    }
  ]
}
```

### Integration Examples

#### n8n Integration
1. Create HTTP Request node
2. Set URL to `http://your-api:8000/mcp/`
3. Add header: `Authorization: Token YOUR_TOKEN`
4. Send MCP protocol requests

#### OpenWebUI Integration
1. Configure MCP server endpoint: `http://your-api:8000/mcp/`
2. Set authentication token
3. Use natural language to query your Django data

#### Claude Desktop Integration
Add to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "django-api": {
      "command": "mcp-client",
      "args": ["--url", "http://your-api:8000/mcp/", "--auth", "Token YOUR_TOKEN"]
    }
  }
}
```

### MCP Management Commands

```bash
# Inspect available MCP tools
python manage.py mcp_inspect

# Start standalone MCP server (if needed)
python manage.py stdio_server
```

---

## Memo Management

Based on the codebase structure, the memo functionality appears to be handled in the `/memo/` endpoint. The exact model structure wasn't fully visible in the explored files, but the endpoint exists at:

```
GET /memo/     # Memo-related endpoints (specific routes TBD)
```

---

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
    "detail": "Error message",
    "code": "error_code"
}
```

Or for field validation errors:

```json
{
    "field_name": ["Field-specific error message"]
}
```

---

## Pagination

List endpoints use Django REST Framework's default pagination:

```json
{
    "count": 100,
    "next": "http://api.example.com/endpoint/?page=3",
    "previous": "http://api.example.com/endpoint/?page=1",
    "results": [...]
}
```

---

## File Uploads

### Image Upload Fields

- `CustomUser.profile_picture` - Profile images stored in `profile_image/`
- `PostImage.image` - Blog post images in `blog/{author_id}/{post_id}/images/`
- `Llmproviders.icon` - Provider icons in `llmprovider_icons/`

### Audio Upload Fields

- `PostAudio.audio` - Audio files in `blog/{author_id}/{post_id}/audio/`
- Supported formats: mp3, wav, m4a, aac, ogg

### Media URL Structure

All uploaded files are accessible via:
```
{BASE_URL}/media/{file_path}
```

---

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:8080` (Expo development)
- `http://127.0.0.1:8080`
- `http://10.20.30.203:8080`
- `http://10.20.30.202:3000` (React development)
- `https://api.nxfs.no:443`
- `https://www.nxfs.no`
- `https://nxfs.no`

Required headers:
- `Content-Type: application/json`
- `Authorization: Bearer <token>`

---

## Development Notes

### Database

- **Development**: SQLite (`db.sqlite3`)
- **Production**: MySQL

### Language Support

The API supports both English and Norwegian (Bokmål) with:
- `LANGUAGE_CODE = 'nb-no'`
- `TIME_ZONE = 'Europe/Oslo'`
- Many models have `_nb` fields for Norwegian translations

### Additional Features

- **WebSocket Support**: Configured with Django Channels
- **Email Backend**: SMTP with Gmail
- **Static Files**: Served from `/static/` and `/media/`
- **Admin Interface**: Available at `/admin/`
- **API Schema**: OpenAPI/Swagger available at `/schema/swagger-ui/`

### Testing

Run tests with:
```bash
python manage.py test
```

---

## Frontend Integration Examples

### React/TypeScript Example

```typescript
// API client setup
const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
    private token: string | null = null;

    setToken(token: string) {
        this.token = token;
    }

    private async request(endpoint: string, options: RequestInit = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(this.token && { Authorization: `Bearer ${this.token}` }),
            ...options.headers,
        };

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    // Authentication
    async login(email: string, password: string) {
        const data = await this.request('/token/', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setToken(data.access);
        return data;
    }

    // Tasks
    async getTasks(): Promise<Task[]> {
        const data = await this.request('/app/tasks/');
        return data.results || data;
    }

    async createTask(task: Partial<Task>): Promise<Task> {
        return this.request('/app/tasks/', {
            method: 'POST',
            body: JSON.stringify(task),
        });
    }

    // Blog posts
    async getBlogPosts(): Promise<BlogPost[]> {
        const data = await this.request('/api/posts/');
        return data.results || data;
    }

    async createBlogPost(post: Partial<BlogPost>): Promise<BlogPost> {
        return this.request('/api/posts/', {
            method: 'POST',
            body: JSON.stringify(post),
        });
    }

    // LLM Providers
    async getLlmProviders(): Promise<LlmProvider[]> {
        const data = await this.request('/app/providers/');
        return data.results || data;
    }
}

export const apiClient = new ApiClient();
```

### React Hook Example

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from './apiClient';

export function useTasks() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                setLoading(true);
                const fetchedTasks = await apiClient.getTasks();
                setTasks(fetchedTasks);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchTasks();
    }, []);

    const createTask = async (taskData: Partial<Task>) => {
        try {
            const newTask = await apiClient.createTask(taskData);
            setTasks(prev => [...prev, newTask]);
            return newTask;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create task');
            throw err;
        }
    };

    return { tasks, loading, error, createTask };
}
```

This documentation provides comprehensive information for integrating a React frontend with your Django REST API, including authentication, CRUD operations for all major models, and practical implementation examples.