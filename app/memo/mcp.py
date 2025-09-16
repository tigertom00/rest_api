from mcp_server import mcp_server, ModelQueryToolset
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, Timeliste, JobberImage, JobberFile
from restAPI.mcp import UserToolset


@mcp_server.tool()
class LeverandorerToolset(ModelQueryToolset):
    """MCP toolset for managing suppliers (leverandører)"""

    model = Leverandorer

    searchable_fields = ['name', 'url']
    filterable_fields = []

    serializable_fields = ['id', 'name', 'url', 'created_at', 'updated_at']


@mcp_server.tool()
class MatriellToolset(ModelQueryToolset):
    """MCP toolset for managing materials (matriell)"""

    model = Matriell

    searchable_fields = ['tittel', 'info', 'el_nr']
    filterable_fields = ['leverandor', 'el_nr']

    serializable_fields = [
        'id', 'el_nr', 'tittel', 'info', 'leverandor',
        'created_at', 'updated_at'
    ]


@mcp_server.tool()
class JobberToolset(ModelQueryToolset):
    """MCP toolset for managing jobs (jobber)"""

    model = Jobber

    searchable_fields = ['tittel', 'adresse', 'beskrivelse', 'telefon_nr']
    filterable_fields = ['ferdig', 'ordre_nr']

    serializable_fields = [
        'ordre_nr', 'tittel', 'adresse', 'telefon_nr', 'beskrivelse',
        'ferdig', 'date', 'created_at', 'updated_at'
    ]


@mcp_server.tool()
class JobbMatriellToolset(ModelQueryToolset):
    """MCP toolset for managing job materials (jobb matriell)"""

    model = JobbMatriell

    searchable_fields = []
    filterable_fields = ['jobb', 'matriell', 'transf']

    serializable_fields = [
        'id', 'antall', 'transf', 'created_at', 'updated_at'
    ]


@mcp_server.tool()
class TimelisteToolset(ModelQueryToolset):
    """MCP toolset for managing time tracking (timeliste)"""

    model = Timeliste

    searchable_fields = ['beskrivelse']
    filterable_fields = ['user', 'jobb', 'dato']

    serializable_fields = [
        'id', 'beskrivelse', 'dato', 'timer', 'created_at', 'updated_at'
    ]


@mcp_server.tool()
class JobberImageToolset(ModelQueryToolset):
    """MCP toolset for managing job images"""

    model = JobberImage

    filterable_fields = ['jobb']

    serializable_fields = ['id', 'created_at']


@mcp_server.tool()
class JobberFileToolset(ModelQueryToolset):
    """MCP toolset for managing job files"""

    model = JobberFile

    filterable_fields = ['jobb']

    serializable_fields = ['id', 'created_at']