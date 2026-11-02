# NEI — Engineering Evidence Protocol (EEP)

**Scope:** How NEI sources, validates, records, and cites technical evidence.
**Phase:** 4 (full), partial in Phase 5.

> This is a protocol, not a source list. No specific journals, standards, or clauses are listed here. The protocol defines what metadata must accompany any source and how formulas move through their lifecycle.

---

## 1. Source metadata

Every source document ingested into NEI must have this metadata record. Unknown fields are `null`, never guessed.

```json
{
  "source_id": "uuid",
  "title": "",
  "author": "",
  "publisher": "",
  "source_type": "regulation|class_rule|standard|textbook|journal|conference|report|manual|other",
  "authority_level": "regulatory|class|standard|academic|vendor|other",
  "edition": "",
  "year": null,
  "doi": null,
  "official_url": null,
  "local_file_path": "",
  "checksum_sha256": "",
  "ingested_at": "",
  "verification_status": "unverified|verified|invalid"
}
```

**Rules:**
- `checksum_sha256` is computed on ingestion. The file is never modified after ingestion.
- `verification_status=unverified` is the default. A source is `verified` only after: identity confirmed, edition/revision confirmed, checksum matches, and applicability to the project scope is documented.
- Never fill a field with a guess. If unknown, `null`.

---

## 2. Source classification

| `source_type` | What it is | Examples (user provides) |
|--------------|-----------|--------------------------|
| `regulation` | IMO instruments, SOLAS, MARPOL amendments | User-supplied IMO publications |
| `class_rule` | BKI, IACS, Lloyd's, DNV rules | User-supplied rule books |
| `standard` | ISO, EN, ASTM standards | User-supplied standards |
| `textbook` | Naval architecture / marine engineering textbooks | User-supplied books |
| `journal` | Peer-reviewed journal articles | User-supplied papers |
| `conference` | Conference proceedings | User-supplied |
| `report` | Technical reports (classification society, government) | User-supplied |
| `manual` | Software vendor documentation | Vendor manuals |
| `other` | Anything not fitting above | — |

**Authority is context-dependent.** A regulation is authoritative for legal compliance in its jurisdiction. A textbook is authoritative for method derivation. A software manual is authoritative for software behaviour. No source outranks all others universally.

---

## 3. Ingestion rules

1. Original file is stored read-only at `data/documents/<source_id>/<filename>`.
2. Checksum (SHA-256) computed and stored before any extraction.
3. Text extraction preserves page numbers, section headings, and table structure.
4. OCR is a last resort and is marked `ocr=true` in the extraction record. OCR-derived equations must be visually verified by the user before use.
5. Extraction errors (missing pages, garbled tables, unreadable figures) are recorded, not silently dropped.
6. LLM-generated summaries are never stored as the source. They are annotations only.
7. Only documents the user is entitled to use are ingested. No redistribution of copyrighted PDFs.

---

## 4. Formula records

A formula record is a versioned, reviewable implementation of a method.

```json
{
  "formula_id": "uuid",
  "name": "",
  "domain": "geometry|hydrostatics|stability|resistance|propulsion|structures|other",
  "equation_text": "",
  "implementation_ref": "nei/engineering/<domain>/<module>.py::function_name",
  "variables": [
    {"name": "", "symbol": "", "unit": "", "description": ""}
  ],
  "canonical_units": "SI",
  "assumptions": [],
  "applicability": [],
  "source_refs": ["source_id_1", "source_id_2"],
  "source_locations": [
    {"source_id": "", "page": null, "section": "", "clause": "", "equation_no": ""}
  ],
  "validation_case_refs": [],
  "review_status": "DRAFT",
  "version": 1,
  "created_at": "",
  "reviewed_by": null,
  "change_log": []
}
```

---

## 5. Formula lifecycle

```
DRAFT
  → SOURCE_ATTACHED        # at least one source_ref with location
  → IMPLEMENTED           # code written, no LLM involvement in the formula itself
  → UNIT_TESTED           # pytest passes; dimensional consistency confirmed
  → REFERENCE_CASE_TESTED # at least one trusted published example matches within tolerance
  → TECHNICAL_REVIEW      # human reviews equation, assumptions, applicability
  → APPROVED_FOR_USE      # production calculations may use this formula
```

**Rules:**
- LLM may propose a formula in DRAFT status only. It cannot advance a formula past DRAFT.
- Only `APPROVED_FOR_USE` formulas produce results marked `VERIFIED`.
- Formulas in earlier lifecycle stages may be used in a clearly marked **research/sandbox mode**, but results are always labelled `UNVERIFIED`.
- A formula can be demoted (e.g., source found to be superseded) by setting `review_status` back to `DRAFT` and recording the reason in `change_log`.

---

## 6. Evidence status

Every calculation result carries an evidence status:

| Status | Meaning |
|--------|---------|
| `VERIFIED` | Source identity confirmed, formula `APPROVED_FOR_USE`, reference case passed, all postconditions met |
| `CONDITIONAL` | Valid only under stated assumptions; some checks incomplete or assumptions not fully satisfied |
| `UNVERIFIED` | Source, formula status, or reference case insufficient. Result is provided but not certified |
| `INVALID` | A known rule, input constraint, or validation check was violated. Result is not usable |

**A `VERIFIED` label is an internal status. It is not class certification or regulatory approval.**

---

## 7. Citation rules

- Every formula, assumption, and result must cite the exact source location: page, section, clause, table, or equation number.
- If the exact location cannot be confirmed, cite the document at the highest verified granularity and mark the citation `LIMITED_GRANULARITY`.
- Never fabricate page numbers, clause numbers, or equation references.
- If a source is paywalled and only the abstract is accessible, label evidence `ABSTRACT_ONLY`.

---

## 8. LLM boundaries

The LLM may:
- Suggest which formula or method to use (from the registry, not from memory)
- Identify which inputs are missing
- Explain a result in plain language
- Flag conflicts between sources for human review

The LLM may **not**:
- Write formula implementations
- Assign `VERIFIED` status to any result
- Invent citations, formula IDs, or source revisions
- Decide regulatory applicability without structured input data
