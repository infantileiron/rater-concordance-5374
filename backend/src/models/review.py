from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class PanelReview(Base):
 __tablename__="panel_reviews"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 run_id:Mapped[str]=mapped_column(ForeignKey("agreement_runs.id"))
 note:Mapped[str]=mapped_column(Text)
 decision:Mapped[str]=mapped_column(String)
 author:Mapped[str]=mapped_column(String)
 created_at:Mapped[str]=mapped_column(String)
