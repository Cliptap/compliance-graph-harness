from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from pydantic import BaseModel
from src.backend.security.auth import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from src.backend.security.dependencies import get_current_user, TokenData
from src.backend.services.user_service import get_user_by_email, get_all_users, create_user, delete_user, reset_user_password

router = APIRouter(tags=["auth"])

class UserOut(BaseModel):
    email: str
    full_name: str
    role: str
    scopes: list[str]

class UserCreate(BaseModel):
    email: str
    full_name: str
    role: str
    password: str

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", ""),
            "scopes": user["scopes"]
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/api/v1/users", response_model=list[UserOut])
async def list_users(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["admin:all"])]
):
    return get_all_users()


@router.post("/api/v1/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserCreate,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["admin:all"])]
):
    if data.role not in ("admin", "medico", "recepcionista"):
        raise HTTPException(status_code=400, detail="Rol inválido. Usar: admin, medico, recepcionista")
    user = create_user(data.email, data.full_name, data.role, data.password)
    if not user:
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    return user


@router.delete("/api/v1/users/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    email: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["admin:all"])]
):
    if email == current_user.username:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    if not delete_user(email):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


class PasswordResetResponse(BaseModel):
    email: str
    new_password: str
    message: str


@router.post("/api/v1/users/{email}/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    email: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["admin:all"])]
):
    new_password = reset_user_password(email)
    if not new_password:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return PasswordResetResponse(
        email=email,
        new_password=new_password,
        message="Contrasena regenerada. Guardala, no se mostrara de nuevo."
    )
