from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from src.backend.schemas.doctor_appointment import (
    DoctorCreate, DoctorUpdate, Doctor,
    AppointmentCreate, AppointmentUpdate, Appointment
)
import src.backend.services.doctor_appointment_service as service

router_doctors = APIRouter()
router_appointments = APIRouter()

# --- Rutas Médicos ---
@router_doctors.post("/", response_model=Doctor)
def create_doctor(doctor: DoctorCreate):
    """
    Registra un nuevo médico en el sistema de acuerdo al PRD Fase 2.
    """
    return service.create_doctor(doctor)

@router_doctors.get("/", response_model=List[Doctor])
def list_doctors():
    """
    Obtiene todos los médicos activos.
    """
    return service.get_all_doctors()

# --- Rutas Citas ---
@router_appointments.post("/", response_model=Appointment)
def agendar_cita(appointment: AppointmentCreate):
    """
    Agenda una nueva cita. 
    Contiene reglas de Medium Governance: Evita double-booking temporal e integridad referencial.
    """
    return service.create_appointment(appointment)

@router_appointments.get("/", response_model=List[Appointment])
def list_agendas(paciente_id: Optional[str] = None, medico_id: Optional[str] = None):
    """
    Visualiza el calendario de citas, filtrable por paciente y médico.
    """
    return service.get_all_appointments(paciente_id, medico_id)

@router_appointments.patch("/{appointment_id}/cancel", response_model=Appointment)
def cancel_cita(appointment_id: str):
    """
    Actualiza el estado de la cita a 'Cancelada'. Libera el bloque de horario para este médico.
    """
    return service.cancel_appointment(appointment_id)
