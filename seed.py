import random
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Импортируй свои модели и сессию из проекта
from database import SessionLocal, engine
from models import Base, User, Category, Expense

# Возможные значения
CURRENCIES = ["USD", "EUR", "RUB", "GBP", "JPY"]
USERS = ["admin", "john", "anna", "mike", "lisa"]
CATEGORIES = ["Еда", "Путешествия", "Развлечения", "Техника", "Канцелярия"]

def random_date(start_date, end_date):
    """Генерация случайной даты между start_date и end_date"""
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start_date + timedelta(seconds=random_second)

async def get_exchange_rate(from_currency: str, to_currency: str = "USD"):
    """Заглушка для конвертации — можно заменить на реальный API"""
    # Пример упрощённого курса
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

async def seed_expenses(db: Session, count=50):
    # Создание пользователей и категорий, если их нет
    for user_name in USERS:
        if not db.query(User).filter(User.name == user_name).first():
            db.add(User(name=user_name))

    for category_name in CATEGORIES:
        if not db.query(Category).filter(Category.name == category_name).first():
            db.add(Category(name=category_name))

    db.commit()

    # Генерация случайных расходов
    for _ in range(count):
        amount = round(random.uniform(1, 500), 2)
        currency = random.choice(CURRENCIES)
        user = random.choice(USERS)
        category = random.choice(CATEGORIES)
        timestamp = random_date(datetime(2023, 1, 1), datetime.now())

        db_user = db.query(User).filter(User.name == user).first()
        db_category = db.query(Category).filter(Category.name == category).first()

        # Конвертация в USD
        rate = await get_exchange_rate(currency, "USD")
        converted_amount = round(amount * rate, 2)

        expense = Expense(
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            category_id=db_category.id,
            user_id=db_user.id,
            timestamp=timestamp
        )
        db.add(expense)

    db.commit()
    print(f"Добавлено {count} записей в базу данных.")

if __name__ == "__main__":
    db = SessionLocal()
    asyncio.run(seed_expenses(db))