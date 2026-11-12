import uuid,csv,io
from sqlalchemy import select
from fastapi import HTTPException
from src.models import Report,PanelReview
from src.services.runs import require_completed
from src.utils.time import now
from src.utils.serialization import serialize
from src.utils.csv import safe_cell
def create(db,payload,user):
 require_completed(db,payload.run_id)
 review=db.scalar(select(PanelReview).where(PanelReview.run_id==payload.run_id).order_by(PanelReview.created_at.desc()))
 if not review or review.decision!="accepted":raise HTTPException(409,"最新复核须为接受后才能归档")
 if db.scalar(select(Report).where(Report.run_id==payload.run_id)):raise HTTPException(409,"本次运行已归档")
 item=Report(id=str(uuid.uuid4()),published_by=user["email"],created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
def export(db,id):
 report=db.get(Report,id)
 if not report:raise HTTPException(404,"报告不存在")
 result=require_completed(db,report.run_id).result;buf=io.StringIO()
 cols=["rater_a","rater_b","complete_tasks","isolated_tasks","kendall_w","kappa","observed_disagreement","expected_disagreement","exact_agreement","reason"]
 writer=csv.DictWriter(buf,cols);writer.writeheader()
 for p in result["pairs"]:writer.writerow({"rater_a":safe_cell(p["rater_a"]),"rater_b":safe_cell(p["rater_b"]),"complete_tasks":result["tasks_complete"],"isolated_tasks":result["tasks_isolated"],"kendall_w":result["kendall"]["value"],**{k:p[k] for k in ("kappa","observed_disagreement","expected_disagreement","exact_agreement","reason")}})
 return "\ufeff"+buf.getvalue()
