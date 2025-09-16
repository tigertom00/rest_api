from mcp_server import mcp_server, ModelQueryToolset
from .models import Task, Project, Category


@mcp_server.tool()
class TasksToolset(ModelQueryToolset):
    """MCP toolset for managing tasks, projects and categories"""

    model = Task

    # Allow these fields to be searched/filtered
    searchable_fields = ['title', 'description', 'status', 'priority', 'notes']
    filterable_fields = ['status', 'priority', 'completed', 'user_id', 'category', 'project']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'title', 'description', 'status', 'priority', 'due_date',
        'completed', 'created_at', 'updated_at', 'estimated_time', 'notes'
    ]


@mcp_server.tool()
class ProjectsToolset(ModelQueryToolset):
    """MCP toolset for managing projects"""

    model = Project

    searchable_fields = ['name', 'description', 'status']
    filterable_fields = ['status', 'completed', 'user_id']

    serializable_fields = [
        'id', 'name', 'description', 'status', 'completed',
        'created_at', 'updated_at'
    ]


@mcp_server.tool()
class CategoriesToolset(ModelQueryToolset):
    """MCP toolset for managing task categories"""

    model = Category

    searchable_fields = ['name', 'slug']
    filterable_fields = ['slug']

    serializable_fields = ['id', 'name', 'slug']