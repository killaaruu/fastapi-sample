from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str

class AdminLogin(BaseModel):
    username: str
    password: str
