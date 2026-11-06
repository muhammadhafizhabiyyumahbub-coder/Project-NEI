"""Deterministic section-based hull geometry preview."""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class HullSection:
    station: float
    half_breadth: float
    height: float


def generate_sections(loa: float, beam: float, draft: float, count: int = 11) -> list[HullSection]:
    """Generate symmetric demi-hull sections for preview and downstream meshing."""
    if count < 3 or count % 2 == 0:
        raise ValueError("section count must be odd and at least 3")
    sections = []
    for index in range(count):
        x = index / (count - 1)
        longitudinal = min(x / 0.12, 1.0, (1.0 - x) / 0.12)
        breadth = (beam / 2.0) * max(0.0, longitudinal) ** 0.5
        sections.append(HullSection(station=round(x * loa, 6), half_breadth=round(breadth, 6), height=draft))
    return sections


def section_manifest(sections: list[HullSection]) -> list[dict]:
    return [asdict(section) for section in sections]


def section_volume(sections: list[HullSection], draft: float) -> float:
    """Estimate volume by trapezoidal integration of rectangular section areas."""
    if len(sections) < 2:
        return 0.0
    areas = [2.0 * section.half_breadth * draft for section in sections]
    return sum(
        (sections[i + 1].station - sections[i].station) * (areas[i] + areas[i + 1]) / 2.0
        for i in range(len(sections) - 1)
    )


def validate_sections(sections: list[HullSection], loa: float, beam: float, draft: float) -> dict:
    """Validate section bounds before any downstream geometry use."""
    stations = [s.station for s in sections]
    valid = (
        len(sections) >= 3
        and all(a < b for a, b in zip(stations, stations[1:]))
        and stations[0] == 0
        and stations[-1] == round(loa, 6)
        and all(0 <= s.half_breadth <= beam / 2 for s in sections)
        and all(s.height == draft for s in sections)
    )
    return {"status": "passed" if valid else "failed", "section_count": len(sections)}


def section_lcg(sections: list[HullSection], draft: float) -> float:
    """Longitudinal center of gravity from section moment method."""
    if len(sections) < 2:
        return 0.0
    areas = [2.0 * section.half_breadth * draft for section in sections]
    moment = sum(areas[i] * sections[i].station for i in range(len(sections)))
    total_area = sum(areas)
    return moment / total_area if total_area > 0 else 0.0
