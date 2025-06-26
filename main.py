import httpx
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from models import Base, Expense, User, Category
from database import engine, SessionLocal, get_db
from schemas import ExpenseCreate, ExpenseOut
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
# Создание таблиц
Base.metadata.create_all(bind=engine)



@app.get("/debug")
async def debug(db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    return {"count": len(expenses), "data": [e.__dict__ for e in expenses]}

# Получение курса валют
async def get_exchange_rate(from_currency: str, to_currency: str = "USD"):
    access_key = "10b64d5e286782031da10173bfd39c11"  # заменить на свой
    url = f"http://apilayer.net/api/live?access_key={access_key}&currencies={to_currency}&source={from_currency}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    try:
        data = response.json()
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")

    if not data.get("success", False):
        raise ValueError(f"API error: {data.get('message', 'Unknown error')}")

    quotes = data.get("quotes")
    if not isinstance(quotes, dict):
        raise ValueError(f"Expected 'quotes' to be a dict, got {type(quotes)}: {quotes}")

    rate_key = f"{from_currency}{to_currency}"
    rate = quotes.get(rate_key)

    if rate is None:
        raise ValueError(f"Rate '{rate_key}' not found in response: {quotes}")

    return rate

# Зависимость для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    result = []
    for e in expenses:
        user = db.query(User).get(e.user_id).name
        category = db.query(Category).get(e.category_id).name
        result.append({
            "id": e.id,
            "amount": e.amount,
            "currency": e.currency,
            "converted_amount": e.converted_amount,
            "category": category,
            "user": user,
            "timestamp": e.timestamp
        })
    return templates.TemplateResponse("index.html", {
        "request": request,
        "expenses": result,
        "success": False
    })


@app.post("/add_expense")
async def add_expense(
    request: Request,
    amount: float = Form(...),
    currency: str = Form(...),
    category: str = Form(...),
    user: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        rate = await get_exchange_rate(currency, "USD")

        if currency != "USD":
            inverse_rate = 1 / rate
            converted_amount = amount * inverse_rate
        else:
            converted_amount = amount * rate

        # Добавляем пользователя, если его нет
        db_user = db.query(User).filter(User.name == user).first()
        if not db_user:
            db_user = User(name=user)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        # Добавляем категорию, если её нет
        db_category = db.query(Category).filter(Category.name == category).first()
        if not db_category:
            db_category = Category(name=category)
            db.add(db_category)
            db.commit()
            db.refresh(db_category)

        # Сохраняем расход
        expense = Expense(
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            category_id=db_category.id,
            user_id=db_user.id
        )
        db.add(expense)
        db.commit()
        print("Expense saved:", expense.id, amount, currency)
        db.refresh(expense)

        return templates.TemplateResponse("index.html", {"request": request, "success": True})

    except ValueError as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Неизвестная ошибка: {str(e)}"}
        )

@app.get("/expenses", response_model=list[ExpenseOut])
def get_expenses(db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    result = []
    for e in expenses:
        user = db.query(User).get(e.user_id).name
        category = db.query(Category).get(e.category_id).name
        result.append(ExpenseOut(
            id=e.id,
            amount=e.amount,
            currency=e.currency,
            converted_amount=e.converted_amount,
            category=category,
            user=user,
            timestamp=e.timestamp
        ))
    return result

@app.post("/delete_expense/{expense_id}")
async def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db.delete(expense)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)
@app.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    result = []
    for e in expenses:
        user = db.query(User).get(e.user_id).name
        category = db.query(Category).get(e.category_id).name
        result.append({
            "id": e.id,
            "amount": e.amount,
            "currency": e.currency,
            "converted_amount": e.converted_amount,
            "category": category,
            "user": user,
            "timestamp": e.timestamp
        })
    return templates.TemplateResponse("admin.html", {"request": request, "expenses": result})

ADMIN_USERS = {
    "admin": "abc123456"  # username: password
}

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
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

def is_admin(request: Request):
    user = request.cookies.get("admin_user")
    if not user or user not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return user

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    target_currency: str = "USD",
    search: str = "",
    user_filter: str = "",
    category_filter: str = "",
    is_admin: str = Depends(is_admin)  # ← Защита здесь
):
    return await _render_expenses(request, db, target_currency, search, user_filter, category_filter)
async def _render_expenses(
    request: Request,
    db: Session,
    target_currency: str = "USD",
    search: str = "",
    user_filter: str = "",
    category_filter: str = ""
):
    query = db.query(Expense)

    # Поиск по пользователю или категории
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.join(User).join(Category).filter(
            User.name.ilike(search_pattern) |
            Category.name.ilike(search_pattern)
        )

    # Фильтр по пользователю
    if user_filter:
        query = query.join(User).filter(User.name == user_filter)

    # Фильтр по категории
    if category_filter:
        query = query.join(Category).filter(Category.name == category_filter)

    expenses = query.all()

    users = db.query(User).all()
    categories = db.query(Category).all()

    result = []
    for e in expenses:
        rate = await get_exchange_rate(e.currency, target_currency)
        converted_amount = e.amount * rate if e.currency != target_currency else e.amount

        result.append({
            "id": e.id,
            "amount": e.amount,
            "currency": e.currency,
            "converted_amount": round(converted_amount, 2),
            "category": db.query(Category).get(e.category_id).name,
            "user": db.query(User).get(e.user_id).name,
            "timestamp": e.timestamp
        })

    all_users = [u.name for u in users]
    all_categories = [c.name for c in categories]

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "expenses": result,
        "target_currency": target_currency,
        "search": search,
        "user_filter": user_filter,
        "category_filter": category_filter,
        "users": all_users,
        "categories": all_categories
    })
def is_admin(request: Request):
    user = request.cookies.get("admin_user")
    if not user or user not in ADMIN_USERS:
        raise HTTPException(status_code=307, detail="Требуется авторизация", headers={"Location": "/login"})
    return user
@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="admin_user")
    return RedirectResponse(url="/login", status_code=303)