from typing import Optional, List
from pydantic import BaseModel, UUID4, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum

class DoctorBase(BaseModel):
    rut: str = Field(..., description="RUT del médico", max_length=12)
    nombre_completo: str = Field(..., description="Nombre completo", max_length=150)
    especialidad: str = Field(..., description="Especialidad médica", max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    activo: bool = True

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=150)
    especialidad: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None

class Doctor(DoctorBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- APPOINTMENTS ---

class AppointmentStatus(str, Enum):
    programada = 'Programada'
    confirmada = 'Confirmada'
    completada = 'Completada'
    cancelada = 'Cancelada'

class AppointmentBase(BaseModel):
    paciente_id: str
    medico_id: str
    fecha_hora: datetime
    duracion_minutos: int = Field(30, gt=0)
    estado: AppointmentStatus = AppointmentStatus.programada
    motivo_consulta: Optional[str] = None

    @field_validator('fecha_hora')
    @classmethod
    def validate_future_date(cls, v):
        if v.replace(tzinfo=None) < datetime.now():
            raise ValueError("No se pueden agendar citas en el pasado.")
        return v

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    duracion_minutos: Optional[int] = Field(None, gt=0)
    estado: Optional[AppointmentStatus] = None
    motivo_consulta: Optional[str] = None

class Appointment(AppointmentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
