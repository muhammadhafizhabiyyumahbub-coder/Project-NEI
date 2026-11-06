"""Independent arithmetic reference case for proxy GZ, not approval evidence."""

import math

from nei.engineering.gz import generate_gz_curve


def test_gz_proxy_matches_independent_trapezoid_reference_case():
    result = generate_gz_curve(
        gm_0_m=1.0,
        beam_m=4.0,
        draft_m=2.0,
        min_angle_deg=0.0,
        max_angle_deg=10.0,
        step_deg=5.0,
    )
    expected = []
    for degrees in (0.0, 5.0, 10.0):
        angle = math.radians(degrees)
        gz = 1.0 * math.sin(angle) + 1.0 * (1.0 - math.cos(angle))
        expected.append(round(gz, 9))
    assert [point["gz_m"] for point in result.points] == expected
    expected_area = sum(
        0.5 * (expected[index] + expected[index + 1]) * math.radians(5.0)
        for index in range(2)
    )
    assert result.area_m0rad == round(expected_area, 9)
    assert result.to_dict()["not_for_approval"] is True
