"""Tests for vessel profile registry."""
import pytest
from nei.engineering.vessel_profiles import (
    VESSEL_PROFILES,
    get_vessel_profile,
    validate_hull_against_profile,
    get_default_block_coefficient,
    get_applicable_formulas,
)


def test_all_profiles_have_required_fields():
    for key, profile in VESSEL_PROFILES.items():
        assert profile.vessel_type
        assert profile.hull_family
        assert profile.loa_min > 0
        assert profile.loa_max > profile.loa_min
        assert profile.beam_min > 0
        assert profile.beam_max > profile.beam_min
        assert profile.depth_min > 0
        assert profile.depth_max > profile.depth_min
        assert 0 < profile.draft_ratio_min < profile.draft_ratio_max < 1
        assert profile.speed_min_kn < profile.speed_max_kn
        assert 0 < profile.block_coefficient_default <= 1


def test_get_vessel_profile_known():
    p = get_vessel_profile("tugboat")
    assert p is not None
    assert p.vessel_type == "Tugboat"


def test_get_vessel_profile_unknown():
    p = get_vessel_profile("unknown_boat")
    assert p is None


def test_validate_hull_against_profile_valid():
    # Tugboat profile: depth 3-5, draft_ratio 0.45-0.55; use depth 5, draft 2.5 => ratio 0.5
    warnings = validate_hull_against_profile(
        {"loa": 30, "beam": 8, "depth": 5, "draft": 2.5, "speed": 12},
        "tugboat",
    )
    assert warnings == []


def test_validate_hull_against_profile_out_of_range():
    warnings = validate_hull_against_profile(
        {"loa": 100, "beam": 8, "depth": 4, "draft": 3, "speed": 12},
        "tugboat",
    )
    assert any("LOA" in w for w in warnings)


def test_validate_hull_against_profile_unknown():
    warnings = validate_hull_against_profile(
        {"loa": 30, "beam": 8, "depth": 4, "draft": 3, "speed": 12},
        "unknown_boat",
    )
    assert any("Unknown" in w for w in warnings)


def test_get_default_block_coefficient():
    assert get_default_block_coefficient("tugboat") == 0.78
    assert get_default_block_coefficient("patrol_boat") == 0.48


def test_get_applicable_formulas():
    assert "displacement_volume" in get_applicable_formulas("ferry")
    assert "metacentric_height" in get_applicable_formulas("general_cargo")