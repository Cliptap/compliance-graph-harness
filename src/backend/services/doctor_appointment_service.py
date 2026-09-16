import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from src.backend.schemas.doctor_appointment import (
    DoctorCreate, DoctorUpdate, Doctor,
    AppointmentCreate, AppointmentUpdate, Appointment, AppointmentStatus
)
from src.backend.services.patient_service import _mock_db as PATIENT_DB # Para validar integridad referencial

# Diccionarios en memoria simulando las tablas DB
DOCTORS_MOCK_DB = {}
APPOINTMENTS_MOCK_DB = {}

def get_all_doctors() -> List[Doctor]:
    return [doc for doc in DOCTORS_MOCK_DB.values() if doc.activo]

def get_doctor(doctor_id: str) -> Doctor:
    doc = DOCTORS_MOCK_DB.get(doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return doc

def create_doctor(doctor: DoctorCreate) -> Doctor:
    if any(d.rut == doctor.rut for d in DOCTORS_MOCK_DB.values()):
        raise HTTPException(status_code=400, detail="Médico con este RUT ya existe")
    
    doc_id = str(uuid.uuid4())
    now = datetime.now()
    new_doc = Doctor(
        id=doc_id,
        created_at=now,
        updated_at=now,
        **doctor.model_dump()
    )
    DOCTORS_MOCK_DB[doc_id] = new_doc
    return new_doc

# --- APPOINTMENTS LOGIC ---

def check_double_booking(medico_id: str, new_start: datetime, duracion: int, exclude_id: str = None):
    new_end = new_start + timedelta(minutes=duracion)
    
    for apt in APPOINTMENTS_MOCK_DB.values():
        if apt.medico_id == medico_id and apt.estado in [AppointmentStatus.programada, AppointmentStatus.confirmada]:
            if exclude_id and apt.id == exclude_id:
                continue
            
            existing_start = apt.fecha_hora.replace(tzinfo=None)
            existing_end = existing_start + timedelta(minutes=apt.duracion_minutos)
            
            # Chequeo de solapamiento
            if new_start < existing_end and new_end > existing_start:
                raise HTTPException(status_code=400, detail="Cruce de horarios detectado (Double-Booking) para este médico.")

def create_appointment(appointment: AppointmentCreate) -> Appointment:
    # 1. Integridad Referencial
    if appointment.paciente_id not in PATIENT_DB:
        raise HTTPException(status_code=404, detail="El paciente referenciado no existe.")
    
    medico = DOCTORS_MOCK_DB.get(appointment.medico_id)
    if not medico or not medico.activo:
        raise HTTPException(status_code=404, detail="El médico referenciado no existe o no está activo.")

    # 2. Prevención de colisiones
    check_double_booking(appointment.medico_id, appointment.fecha_hora.replace(tzinfo=None), appointment.duracion_minutos)

    apt_id = str(uuid.uuid4())
    now = datetime.now()
    new_apt = Appointment(
        id=apt_id,
        created_at=now,
        updated_at=now,
        **appointment.model_dump()
    )
    APPOINTMENTS_MOCK_DB[apt_id] = new_apt
    return new_apt

def get_all_appointments(paciente_id: Optional[str] = None, medico_id: Optional[str] = None) -> List[Appointment]:
    res = list(APPOINTMENTS_MOCK_DB.values())
    if paciente_id:
        res = [a for a in res if a.paciente_id == paciente_id]
    if medico_id:
        res = [a for a in res if a.medico_id == medico_id]
    return sorted(res, key=lambda x: x.fecha_hora)

def cancel_appointment(appointment_id: str) -> Appointment:
    apt = APPOINTMENTS_MOCK_DB.get(appointment_id)
    if not apt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    apt.estado = AppointmentStatus.cancelada
    apt.updated_at = datetime.now()
    return apt