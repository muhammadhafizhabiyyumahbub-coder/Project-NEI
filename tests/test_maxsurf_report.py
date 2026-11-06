from pathlib import Path


def test_maxsurf_engineering_report_preserves_limits():
    report = Path("docs/maxsurf_engineering_verification_report.md").read_text(encoding="utf-8")
    assert "maxsurf.hull_generation_manual = SUPPORTED" in report
    assert "maxsurf.hull_generation_from_nei = UNKNOWN" in report
    assert "Hydrostatic calculations or approval" in report
    assert "Classification, regulatory, or engineering approval" in report
