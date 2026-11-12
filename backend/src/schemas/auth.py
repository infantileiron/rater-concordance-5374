from pydantic import BaseModel,Field
class Login(BaseModel):
 email:str=Field(max_length=120)
 password:str=Field(min_length=1,max_length=120)
