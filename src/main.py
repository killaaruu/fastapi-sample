import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.models import Base
from src.database import engine
from src.routers import expenses, admin
from alembic.config import Config
from alembic import command

# Выполняем миграции при старте
alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)
#Ручки
app.include_router(expenses.router)
app.include_router(admin.router)
app.include_router(expenses.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
