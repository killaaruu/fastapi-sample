from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ExpenseCreate(BaseModel):
    amount: float
    currency: str
    category: str
    user: str

class ExpenseOut(BaseModel):
    id: int
    amount: float
    currency: str
    converted_amount: float
    category: str
    user: str
    timestamp: datetime

    class Config:
        orm_mode = True

class AdminLogin(BaseModel):
    username: str
    password: str