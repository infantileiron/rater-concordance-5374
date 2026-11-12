-- Initial demo schema is created from versioned SQLAlchemy metadata.
-- Unique natural keys: dataset/scale/study name and report.run_id.
-- Existing deployments require reviewed ALTER migrations.
CREATE INDEX IF NOT EXISTS ix_agreement_runs_status ON agreement_runs(status);
