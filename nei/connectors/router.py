"""Mock connector router."""

def route_action(action: str, target: str, params: dict):
    """Route action to mock connector for Alpha 0.1."""
    if target == "rhino":
        return {"status": "mocked", "target": "rhino", "action": action}
    elif target == "solidworks":
        return {"status": "mocked", "target": "solidworks", "action": action}
    elif target == "maxsurf":
        return {"status": "mocked", "target": "maxsurf", "action": action}
    return {"status": "unknown_target"}
