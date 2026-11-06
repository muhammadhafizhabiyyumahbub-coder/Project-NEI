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
