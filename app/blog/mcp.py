from mcp_server import mcp_server, ModelQueryToolset
from .models import BlogPost, Tag, SiteSettings, PostImage, PostAudio, PostYouTube
from restAPI.mcp import UserToolset


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


@mcp_server.tool()
class PostImageToolset(ModelQueryToolset):
    """MCP toolset for managing blog post images"""

    model = PostImage

    searchable_fields = ['alt_text', 'caption']
    filterable_fields = ['post']

    serializable_fields = ['id', 'alt_text', 'caption', 'order']


@mcp_server.tool()
class PostAudioToolset(ModelQueryToolset):
    """MCP toolset for managing blog post audio files"""

    model = PostAudio

    searchable_fields = ['title']
    filterable_fields = ['post']

    serializable_fields = ['id', 'title', 'duration_seconds', 'order']


@mcp_server.tool()
class PostYouTubeToolset(ModelQueryToolset):
    """MCP toolset for managing blog post YouTube videos"""

    model = PostYouTube

    searchable_fields = ['url', 'title', 'video_id']
    filterable_fields = ['post', 'video_id']

    serializable_fields = ['id', 'url', 'video_id', 'title', 'order']