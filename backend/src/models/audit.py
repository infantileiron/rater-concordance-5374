from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 actor:Mapped[str]=mapped_column(String)
 action:Mapped[str]=mapped_column(String)
 status:Mapped[int]=mapped_column(Integer)
 created_at:Mapped[str]=mapped_column(String)
