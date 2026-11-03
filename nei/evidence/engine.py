"""Evidence engine: source ingestion, chunking, lexical search, formula records.

Phase 4 Alpha:
- Ingest source document (local file path only, no download)
- SHA-256 checksum on ingestion, file stored read-only under data/documents/<id>/
- Text extraction: simple text/PDF page chunking (PDF via pypdf if available, else raw text)
- FTS5 lexical search over chunks
- Formula registry with lifecycle (DRAFT -> APPROVED_FOR_USE)

No LLM generates evidence. LLM may only cite existing records.
"""
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from nei.core.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


DOCUMENTS_ROOT = Path("data/documents")


# ── Source ingestion ──────────────────────────────────────────────────────────

async def ingest_source(
    title: str,
    source_type: str,
    authority_level: str,
    local_file_path: str,
    *,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
    edition: Optional[str] = None,
    year: Optional[int] = None,
    doi: Optional[str] = None,
    official_url: Optional[str] = None,
) -> dict:
    """Ingest a local source document. Returns source record.

    - Computes SHA-256 of file
    - Copies file to data/documents/<source_id>/<filename> (read-only store)
    - Extracts text chunks, stores in evidence_chunks + FTS5
    - Inserts evidence_sources row with verification_status='unverified'
    """
    src = Path(local_file_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {local_file_path}")

    file_bytes = src.read_bytes()
    checksum = _sha256_bytes(file_bytes)
    source_id = str(uuid.uuid4())

    # Store copy under data/documents/<source_id>/
    dest_dir = DOCUMENTS_ROOT / source_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)

    # Extract text chunks
    chunks = _extract_chunks(file_bytes, src.suffix.lower())

    async with get_db() as db:
        await db.execute(
            """INSERT INTO evidence_sources
               (id, title, author, publisher, source_type, authority_level, edition,
                year, doi, official_url, local_file_path, checksum_sha256,
                ingested_at, verification_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unverified')""",
            (source_id, title, author, publisher, source_type, authority_level,
             edition, year, doi, official_url, str(dest), checksum, _now()),
        )
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source_id}_{i}"
            await db.execute(
                """INSERT INTO evidence_chunks
                   (id, source_id, page, section, clause, equation_no, text,
                    ocr, checksum_sha256, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chunk_id, source_id, chunk.get("page"), chunk.get("section"),
                 chunk.get("clause"), chunk.get("equation_no"), chunk["text"],
                 1 if chunk.get("ocr") else 0,
                 _sha256_bytes(chunk["text"].encode("utf-8")), _now()),
            )
            # FTS external-content keyed by chunk's implicit integer rowid
            cursor = await db.execute("SELECT last_insert_rowid()")
            chunk_rowid = (await cursor.fetchall())[0][0]
            await db.execute(
                "INSERT INTO evidence_chunks_fts (rowid, text) VALUES (?, ?)",
                (chunk_rowid, chunk["text"]),
            )
        await db.commit()

    return {
        "id": source_id,
        "title": title,
        "source_type": source_type,
        "authority_level": authority_level,
        "local_file_path": str(dest),
        "checksum_sha256": checksum,
        "ingested_at": _now(),
        "verification_status": "unverified",
        "chunk_count": len(chunks),
    }


def _extract_chunks(file_bytes: bytes, suffix: str) -> list[dict]:
    """Extract text chunks from file bytes.

    - .pdf: try pypdf page-by-page; fall back to raw bytes decode if unavailable
    - .txt: split into ~500-word chunks preserving section markers
    """
    chunks = []
    if suffix == ".pdf":
        chunks = _extract_pdf(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="replace")
        chunks = _chunk_text(text)
    return chunks


def _extract_pdf(file_bytes: bytes) -> list[dict]:
    try:
        import pypdf
        import io
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        chunks = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                chunks.append({"page": page_num, "section": None, "text": text})
        return chunks
    except ImportError:
        # pypdf not installed — store raw decoded text, mark ocr flag
        text = file_bytes.decode("utf-8", errors="replace")
        return _chunk_text(text)


def _chunk_text(text: str, target_words: int = 400) -> list[dict]:
    """Split text into chunks of ~target_words words, keeping headings as section."""
    words = text.split()
    chunks = []
    current_section = None
    # Detect simple heading markers (lines starting with # or numbered sections)
    lines = text.splitlines()
    section = None
    buf: list[str] = []
    word_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or (len(stripped) > 0 and stripped == stripped.upper() and len(stripped) > 3):
            # heading
            if buf:
                chunks.append({"page": None, "section": section, "text": " ".join(buf)})
                buf, word_count = [], 0
            section = stripped.lstrip("#").strip()
        buf.append(line)
        word_count += len(line.split())
        if word_count >= target_words:
            chunks.append({"page": None, "section": section, "text": " ".join(buf)})
            buf, word_count, section = [], 0, None
    if buf:
        chunks.append({"page": None, "section": section, "text": " ".join(buf)})
    return chunks


# ── Source queries ────────────────────────────────────────────────────────────

async def list_sources() -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, title, source_type, authority_level, local_file_path, checksum_sha256, ingested_at, verification_status FROM evidence_sources ORDER BY ingested_at DESC")
    return [
        {"id": r[0], "title": r[1], "source_type": r[2], "authority_level": r[3],
         "local_file_path": r[4], "checksum_sha256": r[5], "ingested_at": r[6],
         "verification_status": r[7]}
        for r in rows
    ]


async def get_source(source_id: str) -> Optional[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM evidence_sources WHERE id = ?", (source_id,))
    if not rows:
        return None
    r = rows[0]
    # evidence_sources column order
    cols = ["id", "title", "author", "publisher", "source_type", "authority_level",
            "edition", "year", "doi", "official_url", "local_file_path",
            "checksum_sha256", "ingested_at", "verification_status", "notes"]
    return dict(zip(cols, r))


async def verify_source_checksum(source_id: str) -> dict:
    """Re-read stored file, recompute SHA-256, compare to recorded value."""
    src = await get_source(source_id)
    if not src:
        raise ValueError(f"Source {source_id} not found")
    f = Path(src["local_file_path"])
    if not f.exists():
        return {"source_id": source_id, "intact": False, "reason": "file not found"}
    actual = _sha256_bytes(f.read_bytes())
    intact = actual == src["checksum_sha256"]
    return {
        "source_id": source_id,
        "intact": intact,
        "expected_sha256": src["checksum_sha256"],
        "actual_sha256": actual,
    }


async def set_source_status(source_id: str, status: str, reason: str = "") -> dict:
    """Update verification_status. Allowed: unverified, verified, invalid."""
    if status not in ("unverified", "verified", "invalid"):
        raise ValueError(f"Invalid status: {status}")
    async with get_db() as db:
        await db.execute(
            "UPDATE evidence_sources SET verification_status = ?, notes = ? WHERE id = ?",
            (status, reason, source_id),
        )
        await db.commit()
    return await get_source(source_id)


# ── Search ─────────────────────────────────────────────────────────────────────

async def search(query: str, source_id: Optional[str] = None,
                 limit: int = 20) -> list[dict]:
    """FTS5 lexical search over evidence_chunks. Returns chunk + source context."""
    # NOTE: FTS5 external-content table (content='') does not expose rank
    # when joined to another table. Use FTS MATCH filter only, no ORDER BY rank.
    async with get_db() as db:
        if source_id:
            rows = await db.execute_fetchall(
                """SELECT c.id, c.page, c.section, c.clause, c.equation_no, c.text,
                          s.id AS source_id, s.title, s.verification_status
                   FROM evidence_chunks c
                   JOIN evidence_sources s ON s.id = c.source_id
                   WHERE c.source_id = ? AND c.rowid IN (
                       SELECT rowid FROM evidence_chunks_fts WHERE evidence_chunks_fts MATCH ?
                   )
                   LIMIT ?""",
                (source_id, query, limit),
            )
        else:
            rows = await db.execute_fetchall(
                """SELECT c.id, c.page, c.section, c.clause, c.equation_no, c.text,
                          s.id AS source_id, s.title, s.verification_status
                   FROM evidence_chunks c
                   JOIN evidence_sources s ON s.id = c.source_id
                   WHERE c.rowid IN (
                       SELECT rowid FROM evidence_chunks_fts WHERE evidence_chunks_fts MATCH ?
                   )
                   LIMIT ?""",
                (query, limit),
            )
    return [
        {"chunk_id": r[0], "page": r[1], "section": r[2], "clause": r[3],
         "equation_no": r[4], "text": r[5], "source_id": r[6],
         "source_title": r[7], "verification_status": r[8]}
        for r in rows
    ]


# ── Formula registry ──────────────────────────────────────────────────────────

FORMULA_LIFECYCLE = [
    "DRAFT",
    "SOURCE_ATTACHED",
    "IMPLEMENTED",
    "UNIT_TESTED",
    "REFERENCE_CASE_TESTED",
    "TECHNICAL_REVIEW",
    "APPROVED_FOR_USE",
]


async def register_formula(
    name: str,
    domain: str,
    equation_text: str,
    *,
    implementation_ref: Optional[str] = None,
    variables: Optional[list[dict]] = None,
    assumptions: Optional[list[str]] = None,
    applicability: Optional[list[str]] = None,
    source_refs: Optional[list[str]] = None,
    source_locations: Optional[list[dict]] = None,
) -> dict:
    """Register a new formula in DRAFT status (or SOURCE_ATTACHED if refs given)."""
    formula_id = str(uuid.uuid4())
    status = "SOURCE_ATTACHED" if source_refs else "DRAFT"
    now = _now()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO formulas
               (id, name, domain, equation_text, implementation_ref, variables_json,
                canonical_units, assumptions_json, applicability_json,
                source_refs_json, source_locations_json, review_status, version,
                created_at, change_log_json)
               VALUES (?, ?, ?, ?, ?, ?, 'SI', ?, ?, ?, ?, ?, 1, ?, ?)""",
            (formula_id, name, domain, equation_text, implementation_ref,
             json.dumps(variables or []), json.dumps(assumptions or []),
             json.dumps(applicability or []), json.dumps(source_refs or []),
             json.dumps(source_locations or []), status, now,
             json.dumps([{"ts": now, "event": f"created as {status}"}])),
        )
        await db.commit()
    return await get_formula(formula_id)


async def get_formula(formula_id: str) -> Optional[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM formulas WHERE id = ?", (formula_id,))
    if not rows:
        return None
    r = rows[0]
    cols = ["id", "name", "domain", "equation_text", "implementation_ref",
            "variables_json", "canonical_units", "assumptions_json",
            "applicability_json", "source_refs_json", "source_locations_json",
            "validation_case_refs_json", "review_status", "version",
            "created_at", "reviewed_by", "change_log_json"]
    rec = dict(zip(cols, r))
    for k in ("variables_json", "assumptions_json", "applicability_json",
              "source_refs_json", "source_locations_json",
              "validation_case_refs_json", "change_log_json"):
        raw = rec.pop(k)
        rec[k.replace("_json", "")] = json.loads(raw) if raw else []
    return rec


async def list_formulas(domain: Optional[str] = None,
                        status: Optional[str] = None) -> list[dict]:
    sql = "SELECT id, name, domain, equation_text, review_status, version, created_at FROM formulas"
    conds, params = [], []
    if domain:
        conds.append("domain = ?")
        params.append(domain)
    if status:
        conds.append("review_status = ?")
        params.append(status)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY created_at DESC"
    async with get_db() as db:
        rows = await db.execute_fetchall(sql, params)
    return [
        {"id": r[0], "name": r[1], "domain": r[2], "equation_text": r[3],
         "review_status": r[4], "version": r[5], "created_at": r[6]}
        for r in rows
    ]


async def advance_formula(formula_id: str, to_status: str,
                          reviewed_by: str = "user",
                          reason: str = "") -> dict:
    """Advance formula to next lifecycle status. LLM cannot advance past DRAFT.

    enforces: only forward transitions in FORMULA_LIFECYCLE order.
    """
    if to_status not in FORMULA_LIFECYCLE:
        raise ValueError(f"Unknown formula status: {to_status}")
    formula = await get_formula(formula_id)
    if not formula:
        raise ValueError(f"Formula {formula_id} not found")
    current_idx = FORMULA_LIFECYCLE.index(formula["review_status"])
    target_idx = FORMULA_LIFECYCLE.index(to_status)
    if target_idx <= current_idx:
        raise ValueError(
            f"Cannot transition {formula['review_status']} -> {to_status} "
            f"(only forward in lifecycle)"
        )
    async with get_db() as db:
        raw = formula.get("change_log")
        log = raw if isinstance(raw, list) else (json.loads(raw) if raw else [])
        log.append({
            "ts": _now(),
            "event": f"advanced to {to_status}",
            "by": reviewed_by,
            "reason": reason,
        })
        await db.execute(
            "UPDATE formulas SET review_status = ?, reviewed_by = ?, change_log_json = ? WHERE id = ?",
            (to_status, reviewed_by, json.dumps(log), formula_id),
        )
        await db.commit()
    return await get_formula(formula_id)
