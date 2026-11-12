from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class RatingDataset(Base):
 __tablename__="rating_datasets"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 name:Mapped[str]=mapped_column(String,unique=True)
 source:Mapped[str]=mapped_column(String)
 raters:Mapped[list]=mapped_column(JSON)
 tasks:Mapped[list]=mapped_column(JSON)
 created_at:Mapped[str]=mapped_column(String)
