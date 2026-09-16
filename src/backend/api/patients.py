from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.database import get_db
from src.database.models import Patient
from src.database.repository import BaseRepository
from src.backend.schemas import PatientCreate, PatientResponse
from src.backend.security.dependencies import get_current_user, TokenData

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

def get_patient_repo(db: AsyncSession = Depends(get_db)) -> BaseRepository[Patient]:
    return BaseRepository(Patient, db)

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientCreate,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:write"])],
    repo: BaseRepository[Patient] = Depends(get_patient_repo)
):
    new_patient = await repo.create(patient_in.model_dump())
    return new_patient

@router.get("/", response_model=list[PatientResponse])
async def get_all_patients(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:read"])],
    repo: BaseRepository[Patient] = Depends(get_patient_repo)
):
    patients = await repo.get_all()
    return list(patients)

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:read"])],
    repo: BaseRepository[Patient] = Depends(get_patient_repo)
):
    patient = await repo.get(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Paciente no encontrado o eliminado"
        )
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:write"])],
    repo: BaseRepository[Patient] = Depends(get_patient_repo)
):
    success = await repo.soft_delete(patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Error: Paciente no existe en base activa."
        )

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_in: PatientCreate,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["patients:write"])],
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).where(Patient.id == patient_id, Patient.is_deleted == False)
    result = await session.execute(stmt)
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    patient.name = patient_in.name
    patient.identifier = patient_in.identifier
    patient.birth_date = patient_in.birth_date
    await session.commit()
    await session.refresh(patient)
    return patient
