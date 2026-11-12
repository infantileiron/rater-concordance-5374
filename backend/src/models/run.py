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
