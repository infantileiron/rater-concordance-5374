from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class Report(Base):
 __tablename__="agreement_reports"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 run_id:Mapped[str]=mapped_column(ForeignKey("agreement_runs.id"),unique=True)
 title:Mapped[str]=mapped_column(String)
 published_by:Mapped[str]=mapped_column(String)
 created_at:Mapped[str]=mapped_column(String)
