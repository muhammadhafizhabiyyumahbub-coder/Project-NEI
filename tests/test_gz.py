"""Tests for GZ curve generation and classification baseline."""
from nei.engineering.gz import generate_gz_curve, ClassificationBaseline


def test_gz_curve_is_deterministic_and_not_for_approval():
    gz = generate_gz_curve(gm_0_m=1.5, beam_m=10.0, draft_m=3.0)
    assert gz.status in ("stable", "neutral", "unstable")
    assert gz.to_dict()["not_for_approval"] is True
    assert len(gz.points) > 0
    assert gz.area_m0rad is not None
    # Same inputs → same output (deterministic)
    gz2 = generate_gz_curve(gm_0_m=1.5, beam_m=10.0, draft_m=3.0)
    assert gz.to_dict() == gz2.to_dict()


def test_gz_curve_negative_gm_is_unstable():
    gz = generate_gz_curve(gm_0_m=-0.5, beam_m=10.0, draft_m=3.0)
    assert gz.status == "unstable"


def test_gz_curve_rejects_invalid_inputs():
    import pytest
    with pytest.raises(ValueError):
        generate_gz_curve(gm_0_m=None, beam_m=10.0, draft_m=3.0)
    with pytest.raises(ValueError):
        generate_gz_curve(gm_0_m=1.0, beam_m=0, draft_m=3.0)
    with pytest.raises(ValueError):
        generate_gz_curve(gm_0_m=1.0, beam_m=10.0, draft_m=0)
    with pytest.raises(ValueError):
        generate_gz_curve(gm_0_m=1.0, beam_m=10.0, draft_m=3.0, min_angle_deg=5, max_angle_deg=1)
    with pytest.raises(ValueError):
        generate_gz_curve(gm_0_m=1.0, beam_m=10.0, draft_m=3.0, step_deg=0)


def test_classification_baseline_is_unverified():
    report = ClassificationBaseline.evaluate(gm_m=1.0, area_m0rad=0.07, keel_ratio=0.8)
    assert report["status"] == "UNVERIFIED"
    assert report["compliance_claimed"] is False
    assert report["criteria"]["gm_m"]["verified"] is False
    assert report["criteria"]["area_m0rad"]["verified"] is False
    assert report["criteria"]["keel_ratio"]["verified"] is False


def test_classification_baseline_pass_fails_when_below_threshold():
    report = ClassificationBaseline.evaluate(gm_m=0.0, area_m0rad=0.01, keel_ratio=2.0)
    assert report["criteria"]["gm_m"]["pass"] is False
    assert report["criteria"]["area_m0rad"]["pass"] is False
    assert report["criteria"]["keel_ratio"]["pass"] is False
    assert report["compliance_claimed"] is False
