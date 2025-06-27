# src/routers/admin.py

from fastapi import APIRouter, Depends, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.models import Expense, User, Category
from src.services.auth import is_admin, ADMIN_USERS
from src.dependencies import get_db
from src.services.exchange import get_exchange_rate

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def _render_expenses(
    request: Request,
    db: Session,
    target_currency: str = "USD",
    search: str = "",
    user_filter: str = "",
    category_filter: str = "",
):
    query = db.query(Expense)

    if search:
        search_pattern = f"%{search.lower()}%"
        query = (
            query.join(User)
            .join(Category)
            .filter(
                User.name.ilike(search_pattern) | Category.name.ilike(search_pattern)
            )
        )

    if user_filter:
        query = query.join(User).filter(User.name == user_filter)

    if category_filter:
        query = query.join(Category).filter(Category.name == category_filter)

    expenses = query.all()

    users = db.query(User).all()
    categories = db.query(Category).all()

    result = []
    for e in expenses:
        rate = await get_exchange_rate(e.currency, target_currency)
        converted_amount = (
            e.amount * rate if e.currency != target_currency else e.amount
        )

        result.append(
            {
                "id": e.id,
                "amount": e.amount,
                "currency": e.currency,
                "converted_amount": round(converted_amount, 2),
                "category": db.query(Category).get(e.category_id).name,
                "user": db.query(User).get(e.user_id).name,
                "timestamp": e.timestamp,
            }
        )

    all_users = [u.name for u in users]
    all_categories = [c.name for c in categories]

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "expenses": result,
            "target_currency": target_currency,
            "search": search,
            "user_filter": user_filter,
            "category_filter": category_filter,
            "users": all_users,
            "categories": all_categories,
        },
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    target_currency: str = "USD",
    search: str = "",
    user_filter: str = "",
    category_filter: str = "",
    page: int = 1,
    size: int = 20,
):
    # Запрос к БД странички
    query = db.query(Expense).join(User).join(Category)

    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            User.name.ilike(search_pattern) |
            Category.name.ilike(search_pattern)
        )

    if user_filter:
        query = query.filter(User.name == user_filter)

    if category_filter:
        query = query.filter(Category.name == category_filter)

    total = query.count()
    expenses = query.offset((page - 1) * size).limit(size).all()

    users = [u.name for u in db.query(User).all()]
    categories = [c.name for c in db.query(Category).all()]

    # Расчёт общего количества страниц
    total_pages = (total + size - 1) // size

    result = []
    for e in expenses:
        rate = await get_exchange_rate(e.currency, target_currency)
        converted_amount = round(e.amount * rate, 2) if e.currency != target_currency else e.amount

        result.append({
            "id": e.id,
            "amount": e.amount,
            "currency": e.currency,
            "converted_amount": converted_amount,
            "category": db.query(Category).get(e.category_id).name,
            "user": db.query(User).get(e.user_id).name,
            "timestamp": e.timestamp
        })

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "expenses": result,
        "target_currency": target_currency,
        "search": search,
        "user_filter": user_filter,
        "category_filter": category_filter,
        "users": users,
        "categories": categories,
        "current_page": page,
        "total_pages": total_pages,
        "total": total
    })

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    if ADMIN_USERS.get(username) == password:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="admin_user", value=username)
        return response
    else:
        return {"error": "Неверный логин или пароль"}


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="admin_user")
    return RedirectResponse(url="/login", status_code=303)

@router.post("/delete_expense/{expense_id}")
async def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db.delete(expense)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

def get_pagination(total: int, size: int = 20) -> int:
    return (total + size - 1) // size
