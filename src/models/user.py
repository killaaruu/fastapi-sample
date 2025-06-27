# src/models/user.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.models import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    expenses = relationship("Expense", back_populates="user")
