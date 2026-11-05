from nei.connectors.solidworks2022 import SolidWorks2022Connector
from nei.core.config import settings


def test_solidworks_readonly_inspection():
    connector = SolidWorks2022Connector(settings.solidworks_exe_path)
    info = connector.inspect_active_document("document_info")
    features = connector.inspect_active_document("features")
    assert info["available"]
    assert features["available"]
    assert features["feature_count"] >= 0
    capabilities = {c.name: c.status.value for c in connector.get_capabilities()}
    assert capabilities["sw.get_document_info"] == "SUPPORTED"
    assert capabilities["sw.list_features"] == "SUPPORTED"
