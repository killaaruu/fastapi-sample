# src/models/expenses.py

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from src.models import Base


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    converted_amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
