"""Local executable probe tests; no CAD process is launched."""
from nei.connectors.rhino6.connector import Rhino6Connector
from nei.connectors.maxsurf20 import Maxsurf20Connector
from nei.connectors.solidworks2022 import SolidWorks2022Connector
from nei.core.config import settings


def test_local_cad_executables_detected():
    connectors = [
        Rhino6Connector(settings.rhino_exe_path),
        Maxsurf20Connector(settings.maxsurf_exe_path),
        SolidWorks2022Connector(settings.solidworks_exe_path),
    ]
    assert all(conn.detect().detected for conn in connectors)
    assert all(conn.get_version() for conn in connectors)


def test_local_capability_statuses_remain_honest():
    maxsurf = {c.name: c.status.value for c in Maxsurf20Connector(settings.maxsurf_exe_path).get_capabilities()}
    solidworks = {c.name: c.status.value for c in SolidWorks2022Connector(settings.solidworks_exe_path).get_capabilities()}
    assert maxsurf["maxsurf.inspect_project_file"] == "SUPPORTED"
    assert maxsurf["maxsurf.hull_generation"] == "SUPPORTED"
    assert solidworks["sw.get_document_info"] == "SUPPORTED"
