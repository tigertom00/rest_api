from mcp_server import mcp_server, ModelQueryToolset
from .models import DockerHost, DockerContainer, ContainerStats


@mcp_server.tool()
class DockerHostToolset(ModelQueryToolset):
    """MCP toolset for managing Docker hosts"""

    model = DockerHost

    # Allow these fields to be searched/filtered
    searchable_fields = ['name', 'hostname']
    filterable_fields = ['name', 'hostname', 'is_local', 'is_active']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'name', 'hostname', 'is_local', 'is_active',
        'last_seen', 'created_at'
    ]


@mcp_server.tool()
class DockerContainerToolset(ModelQueryToolset):
    """MCP toolset for managing Docker containers"""

    model = DockerContainer

    # Allow these fields to be searched/filtered
    searchable_fields = ['name', 'image', 'container_id']
    filterable_fields = ['status', 'host', 'image', 'name']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'container_id', 'name', 'image', 'status', 'state',
        'ports', 'labels', 'networks', 'mounts', 'created_at',
        'started_at', 'finished_at', 'updated_at', 'is_running'
    ]


@mcp_server.tool()
class ContainerStatsToolset(ModelQueryToolset):
    """MCP toolset for managing container statistics"""

    model = ContainerStats

    # Allow these fields to be searched/filtered
    searchable_fields = []
    filterable_fields = ['container', 'timestamp']

    # Fields that can be returned in responses
    serializable_fields = [
        'id', 'cpu_percent', 'memory_usage', 'memory_limit', 'memory_percent',
        'network_rx', 'network_tx', 'block_read', 'block_write', 'timestamp'
    ]