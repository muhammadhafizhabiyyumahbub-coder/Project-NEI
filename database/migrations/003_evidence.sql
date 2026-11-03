-- NEI migration 003: evidence engine (Phase 4).
-- Source metadata + extracted text chunks + formula records + calc runs.

CREATE TABLE IF NOT EXISTS evidence_sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    source_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    edition TEXT,
    year INTEGER,
    doi TEXT,
    official_url TEXT,
    local_file_path TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_evidence_sources_type ON evidence_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_evidence_sources_status ON evidence_sources(verification_status);

CREATE TABLE IF NOT EXISTS evidence_chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES evidence_sources(id),
    page INTEGER,
    section TEXT,
    clause TEXT,
    equation_no TEXT,
    text TEXT NOT NULL,
    ocr INTEGER NOT NULL DEFAULT 0,
    checksum_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_chunks_source ON evidence_chunks(source_id);

-- SQLite FTS5 virtual table for lexical search over chunk text.
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_chunks_fts USING fts5(
    text,
    content='',
    tokenize='unicode61'
);

-- Formula lifecycle (Phase 5, created here for Phase 4 formula registration).
CREATE TABLE IF NOT EXISTS formulas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    equation_text TEXT NOT NULL,
    implementation_ref TEXT,
    variables_json TEXT,
    canonical_units TEXT NOT NULL DEFAULT 'SI',
    assumptions_json TEXT,
    applicability_json TEXT,
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    source_locations_json TEXT,
    validation_case_refs_json TEXT,
    review_status TEXT NOT NULL DEFAULT 'DRAFT',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    reviewed_by TEXT,
    change_log_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_formulas_domain ON formulas(domain);
CREATE INDEX IF NOT EXISTS idx_formulas_status ON formulas(review_status);
