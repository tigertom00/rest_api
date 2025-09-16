from mcp_server import mcp_server, ModelQueryToolset
from .models import BlogPost, Tag, SiteSettings


@mcp_server.tool()
class BlogPostToolset(ModelQueryToolset):
    """MCP toolset for managing blog posts"""

    model = BlogPost

    # Allow these fields to be searched/filtered
    searchable_fields = ['title', 'excerpt', 'body_markdown', 'slug']
    filterable_fields = ['status', 'author', 'tags', 'published_at']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'title', 'slug', 'excerpt', 'status', 'published_at',
        'created_at', 'updated_at', 'meta_title', 'meta_description'
    ]


@mcp_server.tool()
class BlogTagToolset(ModelQueryToolset):
    """MCP toolset for managing blog tags"""

    model = Tag

    searchable_fields = ['name', 'slug']
    filterable_fields = ['slug']

    serializable_fields = ['id', 'name', 'slug']


@mcp_server.tool()
class SiteSettingsToolset(ModelQueryToolset):
    """MCP toolset for managing site settings"""

    model = SiteSettings

    filterable_fields = ['featured_author']

    serializable_fields = ['id', 'featured_author']