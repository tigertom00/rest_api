from mcp_server import mcp_server, ModelQueryToolset
from .models import Todo


@mcp_server.tool()
class TodoToolset(ModelQueryToolset):
    """MCP toolset for managing todo items"""

    model = Todo

    # Allow these fields to be searched/filtered
    searchable_fields = ['title']
    filterable_fields = ['completed', 'urgent', 'created_by']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'title', 'completed', 'urgent', 'created_at', 'completed_at'
    ]