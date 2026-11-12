from pydantic import BaseModel,Field
class ReportInput(BaseModel):
 run_id:str
 title:str=Field(min_length=2,max_length=120)
