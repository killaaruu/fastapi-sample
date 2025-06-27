# src/seed.py

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models import User, Category, Expense
from src.database import engine
from src.services.exchange import get_exchange_rate


CURRENCIES = ["USD", "EUR", "RUB", "GBP", "JPY"]
USERS = ["admin", "john", "anna"]
CATEGORIES = ["Еда", "Путешествия", "Развлечения", "Техника", "Канцелярия"]


async def get_fake_exchange_rate(from_currency: str, to_currency: str = "USD"):
    fake_rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "RUB": 74.5,
        "GBP": 0.74,
        "JPY": 110.0
    }

    if from_currency not in fake_rates or to_currency not in fake_rates:
        return 1.0

    rate = fake_rates[from_currency] / fake_rates[to_currency]
    return rate


def seed_expenses(db: Session, count=50):
    # Очистка перед заливкой (опционально)
    db.query(Expense).delete()
    db.query(User).delete()
    db.query(Category).delete()

    print("🌱 Добавляем пользователей...")
    for name in USERS:
        user = User(name=name)
        db.add(user)

    print("📁 Добавляем категории...")
    for name in CATEGORIES:
        category = Category(name=name)
        db.add(category)

    db.commit()

    users = db.query(User).all()
    categories = db.query(Category).all()

    print(f"📈 Генерируем {count} расходов...")
    for _ in range(count):
        amount = round(random.uniform(10, 500), 2)
        currency = random.choice(CURRENCIES)

        rate = asyncio.run(get_exchange_rate(currency, "USD"))
        converted_amount = round(amount * rate, 2)

        user = random.choice(users)
        category = random.choice(categories)

        expense = Expense(
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            category_id=category.id,
            user_id=user.id,
            timestamp=datetime.now()
        )
        db.add(expense)

    db.commit()
    print("✅ Тестовые данные загружены.")


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    seed_expenses(session)