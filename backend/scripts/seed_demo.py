import random,json
from sqlalchemy import select,func
from src.config.database import Base,engine,Session
from src.models import User,RatingDataset,RatingScale,AgreementStudy,AgreementRun,PanelReview,Report
from src.services.analysis import analyze
from src.utils.security import hash_password
from src.utils.time import now
def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ("admin","analyst","viewer"):
   if not db.get(User,role):db.add(User(id=role,email=role+"@songting.demo",password=hash_password("Panel2026!"),role=role))
  levels=[{"code":f"L{i}","label":label} for i,label in enumerate(["明显不足","基本不足","部分符合","基本符合","充分符合"],1)]
  raters=["评委甲","评委乙","评委丙","评委丁"];rng=random.Random(2303);tasks=[]
  for i in range(120):
   base=rng.randint(1,5);ratings={}
   for j,r in enumerate(raters):
    shift=rng.choices([-1,0,1],[.15,.7,.15])[0]-(1 if j==3 else 0)
    ratings[r]=f"L{max(1,min(5,base+shift))}"
   if i in (10,36,87,108):ratings["评委丁"]=None
   tasks.append({"task_id":f"ST-{i+1:03}","group":["摘要任务","检索任务","结构化任务"][i%3],"ratings":ratings})
  if not db.get(RatingDataset,"demo-data"):db.add(RatingDataset(id="demo-data",name="松庭盲评·120任务四评委",source="songting_blind_ratings_202611.json",raters=raters,tasks=tasks,created_at=now()));db.flush()
  if not db.get(RatingScale,"demo-scale"):db.add(RatingScale(id="demo-scale",name="任务质量·五级有序标尺v1",levels=levels,created_at=now()));db.flush()
  if not db.get(AgreementStudy,"demo-study"):db.add(AgreementStudy(id="demo-study",name="四评委·盲评一致性复核",dataset_id="demo-data",scale_id="demo-scale",rater_ids=raters,created_at=now()));db.flush()
  if not db.get(AgreementRun,"demo-run"):db.add(AgreementRun(id="demo-run",study_id="demo-study",status="completed",result=analyze(tasks,raters,levels),error="",created_at=now()));db.flush()
  if not db.get(PanelReview,"demo-review"):db.add(PanelReview(id="demo-review",run_id="demo-run",note="4项缺评分任务已整行隔离，W与全部6对kappa共用116项完整任务。评委丁偏严需结合分歧任务复核，不据指标自动评价人员。",decision="accepted",author="analyst@songting.demo",created_at=now()));db.flush()
  if not db.get(Report,"demo-report"):db.add(Report(id="demo-report",run_id="demo-run",title="松庭盲评·评分标尺校准卷宗",published_by="admin@songting.demo",created_at=now()))
  db.commit();return {m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,RatingDataset,RatingScale,AgreementStudy,AgreementRun,PanelReview,Report)}
if __name__=="__main__":print(json.dumps(seed(),ensure_ascii=False))
