from nei.core.planner import plan_task


def test_handoff_request_produces_three_step_plan():
    plan = plan_task("handoff a 10x3x1 box to solidworks2022")
    assert plan.task_type == "handoff"
    assert len(plan.steps) == 3
    assert plan.steps[0].action == "rhino.create_box_test"
    assert plan.steps[1].action == "rhino.export_copy"
    assert plan.steps[2].action == "solidworks2022.import_copy"


def test_plain_box_request_unchanged():
    plan = plan_task("create a 10x3x1 box in rhino")
    assert plan.task_type == "geometry"
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "rhino.create_box_test"
