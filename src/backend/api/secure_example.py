from typing import Annotated
from fastapi import APIRouter, Security, Depends
from src.backend.security.dependencies import get_current_user, TokenData

router = APIRouter()

# Endpoint protegido con inyección de SecurityScopes. Requiere permisos para leer pacientes.
@router.get("/api/v1/patients", tags=["patients"])
async def read_patients(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:read"])]
):
    # La validación de scopes se delega en get_current_user. Si falla se retorna HTTP 403.
    # Aquí ya sabemos que el usuario tiene 'patients:read' o 'admin:all'
    return [{"id": "123", "name": "Paciente de prueba", "accessed_by": current_user.username}]

# Endpoint protegido para escribir citas médicas
@router.post("/api/v1/appointments", tags=["appointments"])
async def create_appointment(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:write"])]
):
    return {"status": "ok", "msg": "Cita generada de forma segura"}
