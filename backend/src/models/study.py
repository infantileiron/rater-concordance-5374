from sqlalchemy import String,Float,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class AgreementStudy(Base):
 __tablename__="agreement_studies"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 name:Mapped[str]=mapped_column(String,unique=True)
 dataset_id:Mapped[str]=mapped_column(ForeignKey("rating_datasets.id"))
 scale_id:Mapped[str]=mapped_column(ForeignKey("rating_scales.id"))
 rater_ids:Mapped[list]=mapped_column(JSON)
 created_at:Mapped[str]=mapped_column(String)
