from pydantic import BaseModel,Field,model_validator
class Task(BaseModel):
 task_id:str=Field(min_length=1,max_length=60)
 group:str=Field(default="未分组",max_length=60)
 ratings:dict[str,str|None]
class DatasetInput(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 source:str=Field(default="blind_ratings.json",max_length=120)
 raters:list[str]=Field(min_length=2,max_length=8)
 tasks:list[Task]=Field(min_length=2,max_length=2000)
 @model_validator(mode="after")
 def valid(self):
  if len(set(self.raters))!=len(self.raters) or any(not x.strip() or len(x)>60 for x in self.raters):raise ValueError("评委代码须非空、唯一且不超过60字")
  if len({t.task_id for t in self.tasks})!=len(self.tasks):raise ValueError("任务编号不能重复")
  for task in self.tasks:
   if not set(task.ratings)<=set(self.raters):raise ValueError("任务中存在未声明的评委")
   if any(v is not None and (not v or len(v)>30) for v in task.ratings.values()):raise ValueError("类别代码须1至30字，缺失应使用null或省略")
  return self
