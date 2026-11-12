-- 运行恢复与租约字段：支持崩溃自动恢复、并发认领CAS与fencing写入。
-- 新部署由 SQLAlchemy metadata 直接建表；既有部署执行本迁移。
ALTER TABLE agreement_runs ADD COLUMN IF NOT EXISTS attempt INTEGER NOT NULL DEFAULT 0;
ALTER TABLE agreement_runs ADD COLUMN IF NOT EXISTS leased_by VARCHAR NOT NULL DEFAULT '';
ALTER TABLE agreement_runs ADD COLUMN IF NOT EXISTS leased_until VARCHAR NOT NULL DEFAULT '';
ALTER TABLE agreement_runs ADD COLUMN IF NOT EXISTS updated_at VARCHAR NOT NULL DEFAULT '';

-- 中断遗留的running运行：清空租约后由worker启动对账重新认领（attempt保留为历史计数）。
UPDATE agreement_runs
   SET leased_until = '', leased_by = '', updated_at = updated_at
 WHERE status = 'running' AND leased_until <> '';
