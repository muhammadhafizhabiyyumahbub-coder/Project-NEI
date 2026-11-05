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
    # With explicit Cb=0.65 (original test case)
    result2 = hull_preview(HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=4, draft=3, speed=12, block_coefficient=0.65))
    assert result2["calculations"]["displacement_volume_m3"] == 468.0



def test_hull_rejects_draft_at_or_above_depth():
    with pytest.raises(ValidationError, match="Draft must be less than depth"):
        HullDesignRequest(vessel_type="Tugboat", loa=30, beam=8, depth=3, draft=3, speed=12)
