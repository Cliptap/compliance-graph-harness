from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.database.database import get_db
from src.database.models import Practitioner
from src.database.repository import BaseRepository
from src.backend.schemas import PractitionerCreate, PractitionerResponse, PractitionerUpdate
from src.backend.security.dependencies import get_current_user, TokenData
from src.backend.services.user_service import create_user
from sqlalchemy import select
import unicodedata, re, secrets, string

router = APIRouter(prefix="/api/v1/practitioners", tags=["practitioners"])

class PractitionerRepository(BaseRepository[Practitioner]):
    def __init__(self, session: AsyncSession):
        super().__init__(Practitioner, session)

@router.post("/", response_model=PractitionerResponse, status_code=status.HTTP_201_CREATED)
async def create_practitioner(
    practitioner_in: PractitionerCreate, 
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["practitioners:write"])],
    db: AsyncSession = Depends(get_db)):
    repo = PractitionerRepository(db)
    
    # Auto-generar credenciales de usuario si se solicita
    generated_password = None
    if practitioner_in.generate_credentials:
        normalized = unicodedata.normalize('NFKD', practitioner_in.name).encode('ascii', 'ignore').decode('ascii')
        email = re.sub(r'[^a-z0-9]+', '.', normalized.lower().strip()).strip('.') + '@clinic.com'
        password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(14))
        create_user(email, practitioner_in.name, "medico", password)
        practitioner_in.email = email
        generated_password = password
    
    data = practitioner_in.model_dump()
    result = await repo.create({k: v for k, v in data.items() if k != 'generate_credentials'})
    response = PractitionerResponse.model_validate(result)
    if generated_password:
        response.generated_password = generated_password
    return response

@router.get("/", response_model=list[PractitionerResponse])
async def get_all_practitioners(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["practitioners:read"])],
    db: AsyncSession = Depends(get_db)):
    repo = PractitionerRepository(db)
    practitioners = await repo.get_all()
    return list(practitioners)

@router.get("/{practitioner_id}", response_model=PractitionerResponse)
async def get_practitioner(
    practitioner_id: str, 
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["practitioners:read"])],
    db: AsyncSession = Depends(get_db)):
    repo = PractitionerRepository(db)
    practitioner = await repo.get(practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return practitioner

@router.delete("/{practitioner_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_practitioner(
    practitioner_id: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["practitioners:write"])],
    db: AsyncSession = Depends(get_db)):
    repo = PractitionerRepository(db)
    success = await repo.soft_delete(practitioner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Practitioner no encontrado")

@router.put("/{practitioner_id}", response_model=PractitionerResponse)
async def update_practitioner(
    practitioner_id: str,
    practitioner_in: PractitionerUpdate,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["practitioners:write"])],
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Practitioner).where(Practitioner.id == practitioner_id, Practitioner.is_deleted == False)
    result = await session.execute(stmt)
    prac = result.scalars().first()
    if not prac:
        raise HTTPException(status_code=404, detail="Medico no encontrado")
    prac.name = practitioner_in.name
    prac.identifier = practitioner_in.identifier
    prac.specialty = practitioner_in.specialty
    prac.telecom = practitioner_in.telecom
    await session.commit()
    await session.refresh(prac)
    return prac
