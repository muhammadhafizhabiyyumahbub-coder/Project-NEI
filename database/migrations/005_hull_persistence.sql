-- NEI migration 003: add hull_design to tasks
-- Persistence for structured hull parameters

ALTER TABLE tasks ADD COLUMN hull_design_json TEXT;
