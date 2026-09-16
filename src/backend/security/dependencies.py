from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from src.backend.security.auth import SECRET_KEY, ALGORITHM
from src.backend.security.context import current_user_ctx

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "admin:all": "Acceso total",
        "patients:read": "Leer pacientes",
        "patients:write": "Crear/Editar/Eliminar pacientes",
        "practitioners:read": "Leer profesionales",
        "practitioners:write": "Crear/Editar/Eliminar profesionales",
        "appointments:read": "Leer citas",
        "appointments:write": "Crear/Editar/Eliminar citas",
        "audit:read": "Consultar registros de auditoria",
        "audit:delete": "Eliminar registros de auditoria",
    }
)

class TokenData(BaseModel):
    username: str
    scopes: list[str] = []
    roles: list[str] = []

async def get_current_user(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
) -> TokenData:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        token_roles = payload.get("roles", [])
        # Compatibilidad: si el payload tiene "role" (singular), convertirlo
        if not token_roles and payload.get("role"):
            token_roles = [payload["role"]]
        token_data = TokenData(username=username, scopes=token_scopes, roles=token_roles)
        current_user_ctx.set(username)  # propagar a listeners de auditoria
    except (JWTError, ValidationError):
        raise credentials_exception
        
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes and "admin:all" not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
    return token_data
