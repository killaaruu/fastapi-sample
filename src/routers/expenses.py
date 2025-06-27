from fastapi import APIRouter, Depends, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.services.exchange import get_exchange_rate
from src.models import Expense, User, Category
from src.dependencies import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    result = []
    for e in expenses:
        user = db.query(User).get(e.user_id).name
        category = db.query(Category).get(e.category_id).name
        result.append(
            {
                "id": e.id,
                "amount": e.amount,
                "currency": e.currency,
                "converted_amount": e.converted_amount,
                "category": category,
                "user": user,
                "timestamp": e.timestamp,
            }
        )
    return templates.TemplateResponse(
        "index.html", {"request": request, "expenses": result, "success": False}
    )


@router.post("/add_expense")
async def add_expense(
    request: Request,
    amount: float = Form(...),
    currency: str = Form(...),
    category: str = Form(...),
    user: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        rate = await get_exchange_rate(currency, "USD")

        if currency != "USD":
            inverse_rate = 1 / rate
            converted_amount = amount * inverse_rate
        else:
            converted_amount = amount * rate

        db_user = db.query(User).filter(User.name == user).first()
        if not db_user:
            db_user = User(name=user)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        db_category = db.query(Category).filter(Category.name == category).first()
        if not db_category:
            db_category = Category(name=category)
            db.add(db_category)
            db.commit()
            db.refresh(db_category)

        expense = Expense(
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            category_id=db_category.id,
            user_id=db_user.id,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)

        return templates.TemplateResponse(
            "index.html", {"request": request, "success": True}
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": f"Неизвестная ошибка: {str(e)}"}
        )


@router.get("/expenses")
def get_expenses(db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    result = []
    for e in expenses:
        user = db.query(User).get(e.user_id).name
        category = db.query(Category).get(e.category_id).name
        result.append(
            {
                "id": e.id,
                "amount": e.amount,
                "currency": e.currency,
                "converted_amount": e.converted_amount,
                "category": category,
                "user": user,
                "timestamp": e.timestamp,
            }
        )
    return result
