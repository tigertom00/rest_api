from mcp_server import mcp_server, ModelQueryToolset
from .models import CustomUser, UserEmail, UserPhone


@mcp_server.tool()
class UserToolset(ModelQueryToolset):
    """MCP toolset for managing users"""

    model = CustomUser

    # Allow these fields to be searched/filtered
    searchable_fields = ['username', 'email', 'display_name', 'clerk_user_id']
    filterable_fields = ['email', 'username', 'is_active', 'is_staff', 'dark_mode', 'language', 'clerk_user_id']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'username', 'email', 'display_name', 'date_of_birth',
        'address', 'city', 'country', 'website', 'phone', 'dark_mode',
        'language', 'is_active', 'date_joined', 'last_login'
    ]


@mcp_server.tool()
class UserEmailToolset(ModelQueryToolset):
    """MCP toolset for managing user emails"""

    model = UserEmail

    searchable_fields = ['email']
    filterable_fields = ['is_primary', 'is_verified', 'user']

    serializable_fields = ['id', 'email', 'is_primary', 'is_verified']


@mcp_server.tool()
class UserPhoneToolset(ModelQueryToolset):
    """MCP toolset for managing user phone numbers"""

    model = UserPhone

    searchable_fields = ['phone_nr']
    filterable_fields = ['is_primary', 'is_verified', 'user']

    serializable_fields = ['id', 'phone_nr', 'is_primary', 'is_verified']