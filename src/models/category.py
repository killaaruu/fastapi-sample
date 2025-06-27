# src/models/category.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.models import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    expenses = relationship("Expense", back_populates="category")
