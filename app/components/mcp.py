from mcp_server import mcp_server, ModelQueryToolset
from .models import Tag, Llmproviders


@mcp_server.tool()
class ComponentTagToolset(ModelQueryToolset):
    """MCP toolset for managing component tags"""

    model = Tag

    searchable_fields = ['name_en', 'name_no']
    filterable_fields = []

    serializable_fields = ['id', 'name_en', 'name_no']


@mcp_server.tool()
class LlmprovidersToolset(ModelQueryToolset):
    """MCP toolset for managing LLM providers"""

    model = Llmproviders

    searchable_fields = ['name', 'description', 'description_nb']
    filterable_fields = ['pricing', 'tags']

    serializable_fields = [
        'id', 'name', 'url', 'description', 'description_nb',
        'strengths_en', 'strengths_no', 'pricing', 'pricing_nb',
        'created_at', 'updated_at'
    ]