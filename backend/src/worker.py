from pathlib import Path
import redis,traceback
from sqlalchemy import select
from src.config.settings import REDIS_URL
from src.config.database import Session
from src.models import AgreementRun,AgreementStudy,RatingDataset,RatingScale
from src.services.analysis import analyze
client=redis.Redis.from_url(REDIS_URL);heartbeat=Path("/artifacts/worker-heartbeat")
def execute(id):
 with Session() as db:
  run=db.get(AgreementRun,id)
  if not run or run.status not in ("queued","running"):return
  run.status="running";db.commit()
  try:
   study=db.get(AgreementStudy,run.study_id);dataset=db.get(RatingDataset,study.dataset_id);scale=db.get(RatingScale,study.scale_id)
   run.result=analyze(dataset.tasks,study.rater_ids,scale.levels);run.status="completed"
  except Exception as e:run.error=str(e);run.status="failed";traceback.print_exc()
  db.commit()
with Session() as db:
 for id in db.scalars(select(AgreementRun.id).where(AgreementRun.status.in_(["queued","running"]))):client.lpush("rater-concordance:jobs",id)
while True:
 heartbeat.touch();job=client.brpop("rater-concordance:jobs",timeout=1)
 if job:execute(job[1].decode())
