import os
DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg://rater:rater-demo@db/rater")
REDIS_URL=os.getenv("REDIS_URL","redis://redis:6379/0")
JWT_SECRET=os.getenv("JWT_SECRET","rater-concordance-development-secret-change")
SEED_DEMO=os.getenv("SEED_DEMO","true").lower()=="true"
# 运行租约：worker认领后持有的最长时长，心跳在到期前续租；崩溃后超过此时长可被其他worker抢占
WORKER_LEASE_SECONDS=float(os.getenv("WORKER_LEASE_SECONDS","30"))
# 对账周期：周期性把排队中与租约过期的运行重新投递
WORKER_RECONCILE_SECONDS=float(os.getenv("WORKER_RECONCILE_SECONDS","15"))
JOB_QUEUE_KEY="rater-concordance:jobs"
