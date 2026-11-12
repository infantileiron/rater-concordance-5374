from pydantic import BaseModel,Field
from typing import Literal
class ReviewInput(BaseModel):
 run_id:str
 note:str=Field(min_length=8,max_length=2000)
 decision:Literal["accepted","needs_attention"]
