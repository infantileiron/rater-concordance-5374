from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class AgreementRun(Base):
 __tablename__="agreement_runs"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 study_id:Mapped[str]=mapped_column(ForeignKey("agreement_studies.id"))
 status:Mapped[str]=mapped_column(String)
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default="")
 created_at:Mapped[str]=mapped_column(String)
 # 认领与租约：attempt为单调递增的fencing令牌，leased_by/leased_until标识当前执行者及租约截止时间
 attempt:Mapped[int]=mapped_column(Integer,default=0)
 leased_by:Mapped[str]=mapped_column(String,default="")
 leased_until:Mapped[str]=mapped_column(String,default="")
 updated_at:Mapped[str]=mapped_column(String,default="")
