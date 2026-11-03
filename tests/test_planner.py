"""Planner tests: template + LLM-fallback paths."""
import json
from nei.core.planner import plan_task, plan_from_llm, Plan, PlanStep


def test_box_with_dims():
    plan = plan_task("create a 10x3x1 box in Rhino 6")
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.action == "rhino.create_box_test"
    assert step.params["length"] == 10.0
    assert step.params["width"] == 3.0
    assert step.params["height"] == 1.0
    assert step.risk_level == "L1"


def test_box_with_decimal_dims():
    plan = plan_task("create a 12.5x4.2x2.1 box")
    step = plan.steps[0]
    assert step.params["length"] == 12.5
    assert step.params["width"] == 4.2
    assert step.params["height"] == 2.1


def test_box_missing_dims_uses_defaults():
    plan = plan_task("create a box in rhino")
    step = plan.steps[0]
    assert step.params["length"] == 10.0
    assert step.params["width"] == 3.0
    assert step.params["height"] == 1.0


def test_non_box_returns_no_steps():
    plan = plan_task("run a hydrostatics calculation")
    assert len(plan.steps) == 0
    assert "action_type" in plan.required_inputs


def test_llm_fallback_produces_action():
    def fake_llm(prompt):
        return json.dumps({"action": "rhino.inspect_objects", "params": {"object_ids": ["abc"]}})

    plan = plan_from_llm("inspect object abc", task_type="geometry", llm_fn=fake_llm)
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "rhino.inspect_objects"


def test_llm_fallback_bad_json_returns_template():
    def fake_llm(prompt):
        return "not json"

    plan = plan_from_llm("create a 5x5x5 box", task_type="geometry", llm_fn=fake_llm)
    # Falls back to template (box match)
    assert len(plan.steps) == 1
    assert plan.steps[0].params["length"] == 5.0


def test_llm_disallowed_action_falls_back():
    def fake_llm(prompt):
        return json.dumps({"action": "rhino.delete_all_objects", "params": {}})

    plan = plan_from_llm("delete everything", task_type="geometry", llm_fn=fake_llm)
    # Non-box, no template → empty steps with required_inputs
    assert len(plan.steps) == 0


def test_box_plan_serializes_to_dict():
    plan = plan_task("create a 10x3x1 box")
    d = {
        "task_type": plan.task_type,
        "steps": [{"action": s.action, "risk_level": s.risk_level, "params": s.params}
                   for s in plan.steps],
        "notes": plan.notes,
    }
    assert json.loads(json.dumps(d))["steps"][0]["action"] == "rhino.create_box_test"
