from pydantic import BaseModel,Field,model_validator
class StudyInput(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 dataset_id:str
 scale_id:str
 rater_ids:list[str]=Field(min_length=2,max_length=8)
 @model_validator(mode="after")
 def unique(self):
  if len(set(self.rater_ids))!=len(self.rater_ids):raise ValueError("不能重复选择评委")
  return self
