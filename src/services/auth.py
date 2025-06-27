# src/services/auth.py

from fastapi import HTTPException, Request

ADMIN_USERS = {"admin": "abc123456"}


def is_admin(request: Request):
    user = request.cookies.get("admin_user")
    if not user or ADMIN_USERS.get(user) is None:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return user
