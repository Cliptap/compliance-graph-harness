from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.database.database import get_db
from src.database.models import Appointment, Patient, Practitioner
from src.database.repository import BaseRepository
from src.backend.schemas import AppointmentCreate, AppointmentResponse
from src.backend.security.dependencies import get_current_user, TokenData
from sqlalchemy import select, and_
from datetime import datetime, timezone
from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: str

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])

class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Appointment, session)

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate, 
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:write"])],
    db: AsyncSession = Depends(get_db)):
    # Validar fechas
    now = datetime.now(timezone.utc)
    if appointment_in.start_time < now:
        raise HTTPException(status_code=400, detail="No se puede agendar una cita en el pasado")
    if appointment_in.end_time <= appointment_in.start_time:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")
    # Validar que el paciente existe y no esta eliminado
    patient = await db.execute(
        select(Patient).where(Patient.id == appointment_in.patient_id, Patient.is_deleted == False)
    )
    if not patient.scalars().first():
        raise HTTPException(status_code=400, detail="El paciente no existe o fue eliminado")
    # Validar que el medico existe y no esta eliminado
    practitioner = await db.execute(
        select(Practitioner).where(Practitioner.id == appointment_in.practitioner_id, Practitioner.is_deleted == False)
    )
    if not practitioner.scalars().first():
        raise HTTPException(status_code=400, detail="El medico no existe o fue eliminado")
    # Validar double-booking para el mismo medico
    overlap = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.practitioner_id == appointment_in.practitioner_id,
                Appointment.is_deleted == False,
                Appointment.start_time < appointment_in.end_time,
                Appointment.end_time > appointment_in.start_time
            )
        )
    )
    if overlap.scalars().first():
        raise HTTPException(status_code=400, detail="El medico ya tiene una cita en ese horario")
    repo = AppointmentRepository(db)
    return await repo.create(appointment_in.model_dump())

@router.get("/", response_model=list[AppointmentResponse])
async def get_all_appointments(
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:read"])],
    db: AsyncSession = Depends(get_db)):
    repo = AppointmentRepository(db)
    appointments = await repo.get_all()
    return list(appointments)

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str, 
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:read"])],
    db: AsyncSession = Depends(get_db)):
    repo = AppointmentRepository(db)
    appointment = await repo.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.delete("/{appointment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:write"])],
    db: AsyncSession = Depends(get_db)):
    repo = AppointmentRepository(db)
    success = await repo.soft_delete(appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment no encontrada")

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    status_update: StatusUpdate,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["appointments:write"])],
    db: AsyncSession = Depends(get_db)):
    repo = AppointmentRepository(db)
    appointment = await repo.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    # Si es medico, solo puede editar sus propias citas (vinculado por email)
    is_medico = "medico" in (current_user.roles or [])
    if is_medico:
        prac = await db.execute(
            select(Practitioner).where(
                Practitioner.email == current_user.username,
                Practitioner.is_deleted == False
            )
        )
        assigned_prac = prac.scalars().first()
        if not assigned_prac or appointment.practitioner_id != assigned_prac.id:
            raise HTTPException(status_code=403, detail="Solo puede modificar sus propias citas")
    valid = {"agendada","confirmada","en_curso","completada","cancelada","no_asiste"}
    if status_update.status not in valid:
        raise HTTPException(status_code=400, detail=f"Estado invalido. Usar: {', '.join(sorted(valid))}")
    appointment.status = status_update.status
    await db.commit()
    await db.refresh(appointment)
    return appointment
