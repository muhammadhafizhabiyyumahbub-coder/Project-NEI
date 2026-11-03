-- NEI migration 004: engineering core (Phase 5).
-- Deterministic calculation runs + formula lifecycle state.

CREATE TABLE IF NOT EXISTS calculation_runs (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    formula_id TEXT NOT NULL REFERENCES formulas(id),
    inputs_json TEXT NOT NULL,
    result_json TEXT NOT NULL,
    status TEXT NOT NULL,
    trace_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calc_runs_task ON calculation_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_calc_runs_formula ON calculation_runs(formula_id);
CREATE INDEX IF NOT EXISTS idx_calc_runs_status ON calculation_runs(status);
