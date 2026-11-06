from nei.engineering.report import build_hull_report


def test_hull_report_is_deterministic_and_not_for_approval():
    report = build_hull_report(
        task_id="task-1",
        hull={"loa": 30, "beam": 8, "draft": 2.5},
        preview={"calculations": {"displacement_volume_m3": 600}},
    )
    assert report["status"] == "NOT_FOR_APPROVAL"
    assert report["report_sha256"]
    assert "No hydrostatic solver" in report["limitations"][1]
