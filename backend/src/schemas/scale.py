from pydantic import BaseModel,Field,model_validator
class Level(BaseModel):
 code:str=Field(min_length=1,max_length=30)
 label:str=Field(min_length=1,max_length=60)
class ScaleInput(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 levels:list[Level]=Field(min_length=5,max_length=5)
 @model_validator(mode="after")
 def unique(self):
  if len({x.code for x in self.levels})!=5:raise ValueError("五级标尺代码必须唯一，列表顺序即1至5级序号")
  return self
