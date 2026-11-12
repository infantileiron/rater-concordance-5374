from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class RatingScale(Base):
 __tablename__="rating_scales"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 name:Mapped[str]=mapped_column(String,unique=True)
 levels:Mapped[list]=mapped_column(JSON)
 created_at:Mapped[str]=mapped_column(String)
