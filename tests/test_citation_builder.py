"""Tests for citation builder (EEP §7)."""
from nei.evidence.citation_builder import build_citation


def test_citation_exact_location():
    chunk = {"page": 45, "section": "3.2.1", "clause": "A", "equation_no": "2"}
    source = {"title": "Stability Manual", "edition": "2nd", "year": 2020}
    assert build_citation(chunk, source) == (
        "Stability Manual, 2nd, 2020 (3.2.1, Clause A, Eq. 2, p. 45)"
    )


def test_citation_minimal_location():
    chunk = {"text": "something"}
    source = {"title": "Stability Manual", "edition": None, "year": None}
    assert build_citation(chunk, source) == (
        "Stability Manual (LIMITED_GRANULARITY)"
    )


def test_citation_page_only():
    chunk = {"page": 12}
    source = {"title": "Manual", "edition": None, "year": None}
    assert build_citation(chunk, source) == "Manual (p. 12)"


def test_citation_no_title():
    chunk = {"section": "1.1"}
    source = {"title": None, "edition": None, "year": None}
    assert build_citation(chunk, source) == "Unknown source (1.1)"
