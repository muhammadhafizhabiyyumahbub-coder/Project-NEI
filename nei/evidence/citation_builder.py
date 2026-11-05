"""Citation builder for evidence chunks (EEP §7).

Rules:
- Cite exact location when available (page, section, clause, equation).
- If no location is available, cite at document level and append
  LIMITED_GRANULARITY — never fabricate page/clause/equation numbers.
"""
from typing import Optional


def build_citation(chunk: dict, source: dict) -> str:
    """Build a citation string from a chunk record and its source record."""
    # Source part: title + edition/year when present
    bits = [source.get("title") or "Unknown source"]
    if source.get("edition"):
        bits.append(source["edition"])
    if source.get("year"):
        bits.append(str(source["year"]))
    citation = ", ".join(bits)

    # Location part: only fields the chunk actually has
    loc: list[str] = []
    if chunk.get("section"):
        loc.append(chunk["section"])
    _append(loc, "Clause {}", chunk.get("clause"))
    _append(loc, "Eq. {}", chunk.get("equation_no"))
    if chunk.get("page") is not None:
        loc.append(f"p. {chunk['page']}")

    if loc:
        citation += f" ({', '.join(loc)})"
    else:
        citation += " (LIMITED_GRANULARITY)"
    return citation


def _append(loc: list[str], fmt: str, value: Optional[str]) -> None:
    if value:
        loc.append(fmt.format(value))
