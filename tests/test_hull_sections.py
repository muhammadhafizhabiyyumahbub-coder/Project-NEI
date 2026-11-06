import pytest
from nei.engineering.geometry.hull_sections import generate_sections, section_manifest, section_volume, validate_sections, section_lcg


def test_section_generator_is_symmetric_and_deterministic():
    sections = generate_sections(30, 8, 2.5)
    assert len(sections) == 11
    assert sections[0].half_breadth == 0
    assert sections[-1].half_breadth == 0
    assert sections[5].half_breadth == 4
    assert section_manifest(sections) == section_manifest(generate_sections(30, 8, 2.5))
    assert section_volume(sections, 2.5) > 0
    assert validate_sections(sections, 30, 8, 2.5)["status"] == "passed"
    lcg = section_lcg(sections, 2.5)
    assert lcg > 0
    assert lcg < 30


def test_section_count_must_be_odd():
    with pytest.raises(ValueError):
        generate_sections(30, 8, 2.5, count=10)
