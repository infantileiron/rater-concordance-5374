# 运行恢复 / 幂等 / 抢占验证（gb-2303）

仅依赖 SQLAlchemy、redis、pytest，使用文件型 SQLite（WAL）与假队列，不依赖外部
Postgres/Redis。被测的条件更新（CAS）、attempt fencing、租约与对账均走真实
SQLAlchemy 语句，与生产 Postgres 行锁语义一致。

运行：

```sh
pip install SQLAlchemy==2.0.41 redis==5.2.1 pytest
python3 -m pytest -q
```

场景覆盖：

- `test_jobs.py`：queued/过期running 的条件认领、重复投递只认领一次、终态 no-op、
  fencing 拦截旧执行者的完成/失败写入、租约续租与过期抢占、对账查询与重复入队安全性。
- `test_worker.py`：中断后同一运行编号自动恢复、重复投递结果只发布一次、抢占后旧结果
  无法覆盖、队列故障下 worker 不中断并在恢复后续算、创建时队列故障保留 queued、
  计算失败落终态不重复投递、心跳为长计算保租约、恢复后评分口径/隔离/校验码不变、
  复核与一run一次归档关系不变。
- `test_concurrent_workers.py`：两个真实 `run_forever` 循环并发消费同一队列且每运行
  重复投递，每个运行仅发布一次结果（attempt 停在 1）。
