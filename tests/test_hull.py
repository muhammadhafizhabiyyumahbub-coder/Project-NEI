import pytest
from pydantic import ValidationError
from nei.engineering.hull import HullDesignRequest, hull_preview


def test_hull_preview_calculates_displacement_and_froude():
    # with default profile Cb (0.78)
    result = hull_preview(HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12))
    assert result["status"] == "PREVIEW_ONLY"
    # Expected with default Cb for tugboat 0.78
    assert result["calculations"]["displacement_volume_m3"] == 561.6
    assert result["calculations"]["froude_number"] > 0
    assert result["calculations"]["waterplane_area_m2"] == 240.0
    assert result["calculations"]["center_of_buoyancy_z_m"] == 1.5
    assert result["calculations"]["stability_status"] == "not_verified"
    stable = hull_preview(HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12, kg=2.0, km=2.5))
    assert stable["calculations"]["metacentric_height_m"] == 0.5
    assert stable["calculations"]["stability_status"] == "stable"
    loaded = hull_preview(HullDesignRequest(
        vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12,
        loading_conditions=[{"id": "full_load", "kg": 2.0, "km": 2.5}, {"id": "ballast", "kg": 3.0, "km": 2.5}],
    ))
    assert loaded["calculations"]["loading_conditions"][0]["status"] == "stable"
    assert loaded["calculations"]["loading_conditions"][1]["status"] == "unstable"
    corrected = hull_preview(HullDesignRequest(
        vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12,
        loading_conditions=[{"id": "tank", "kg": 2.0, "km": 2.5, "free_surface_moment": 300.0}],
    ))
    assert corrected["calculations"]["loading_conditions"][0]["gm_m"] < 0.5
    # With explicit Cb=0.65 (original test case)
    result2 = hull_preview(HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12, block_coefficient=0.65))
    assert result2["calculations"]["displacement_volume_m3"] == 468.0



def test_hull_rejects_draft_at_or_above_depth():
    with pytest.raises(ValidationError, match="Draft must be less than depth"):
        HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=3, draft=3, speed=12)
