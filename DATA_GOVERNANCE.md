# NEI — Data Governance

**Scope:** File integrity, backup, retention, and document rights for all data NEI stores locally.

---

## 1. Data layout

```
data/
├── nei.db                    # SQLite database (WAL mode)
├── documents/                # Original source documents (read-only after ingestion)
│   └── <source_id>/
│       ├── <original_file>   # immutable
│       └── metadata.json     # source metadata (checksum, status, etc.)
├── indexes/                  # Search indexes (rebuildable)
├── formulas/                 # Formula records and test cases
├── projects/
│   └── <project_id>/
│       └── artifacts/
│           ├── <artifact files>
│           ├── scripts/       # Executed scripts (immutable after run)
│           └── manifest.json  # SHA-256 manifest for this project
├── logs/                     # Application logs (rotating)
└── backups/
    └── nei_<YYYYMMDD_HHMM>.db
```

`data/` is in `.gitignore`. It is the user's local data root, not part of the code repository.

---

## 2. File integrity

| File type | Integrity mechanism |
|-----------|-------------------|
| `nei.db` | SQLite checksums are internal; WAL provides crash safety. No application-level hash. |
| Source documents | SHA-256 computed on ingestion. `checksum_sha256` stored in `evidence_sources`. On re-read: hash verified; mismatch → `artifact_corrupt` error, source marked `INVALID`. |
| Artifacts (outputs) | SHA-256 computed on write, stored in `artifacts` table. Verified on every read. Mismatch → `status=CORRUPT` in `artifacts` table. |
| Scripts | SHA-256 computed before execution, stored in `audit_events.script_hash`. Script file preserved at `data/projects/<id>/artifacts/scripts/`. |
| Manifest | `data/projects/<id>/artifacts/manifest.json` lists all artifacts with SHA-256. Regenerated on backup. |

**Rule: No file is ever silently modified after its hash is recorded.** Corrections produce new files with new hashes.

---

## 3. Backup

| Trigger | Method | Retention |
|---------|--------|-----------|
| Manual (user action) | `POST /api/v1/backup` → `VACUUM INTO 'data/backups/nei_<ts>.db'` + copy `data/projects/` and `data/documents/` to `data/backups/<ts>/` | Until user deletes |
| Daily (automatic, if `data/` size changed since last backup) | Same as manual, triggered at startup or after a task completes | Until user deletes |
| Before approved modification (L2+) | `VACUUM INTO` to `data/backups/pre_<task_id>.db` | Until user deletes |

**Backup does not delete older backups.** The user manages `data/backups/` retention.

**Restore:** User copies `nei.db` and project directories back. No automatic restore tool in MVP.

---

## 4. Retention policy

| Data | Retention |
|------|-----------|
| `audit_events` | Indefinite. No automatic deletion. |
| `artifacts` | Until user deletes the project. |
| `evidence_sources` / `evidence_chunks` | Until user deletes the source. Original file is never auto-deleted. |
| `model_usage` | Indefinite. |
| `logs/` | Rotating: 5 files × 5 MB. Older files auto-deleted by `RotatingFileHandler`. |
| `backups/` | Until user deletes. |

**No automatic deletion of engineering data.** All retention is user-controlled.

---

## 5. Document rights

- NEI ingests only documents the user is entitled to use.
- Original files are stored read-only. NEI does not redistribute source PDFs.
- Extracted text and citations follow the same rights boundary as the original.
- The `source_registry` records which sources have been ingested and their checksums.
- If a source's rights status changes (e.g., a class rule is withdrawn), the user manually updates `verification_status`. NEI does not auto-detect status changes.
- OCR-derived content is marked `ocr=true` and visually verified before use in calculations.

---

## 6. Data deletion

| What | How | Consequence |
|------|-----|-------------|
| Delete a project | `DELETE /api/v1/projects/{id}` (requires no active tasks) | All tasks, artifacts, and audit events for that project are deleted. |
| Delete a source | `DELETE /api/v1/evidence/sources/{id}` | Source file and chunks deleted. Formulas referencing it are marked `SOURCE_MISSING`. |
| Delete a backup | User deletes file from `data/backups/` | No application-level action. |
| Wipe all data | User deletes `data/` directory | No application-level action. Irreversible. |

**No soft-delete in MVP.** Deletion is immediate and irreversible. Document this clearly in UI confirmation dialogs.
