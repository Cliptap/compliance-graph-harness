from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import date
from typing import Optional
from enum import Enum
import re

class SexoEnum(str, Enum):
    masculino = 'M'
    femenino = 'F'
    otro = 'O'

class PrevisionEnum(str, Enum):
    fonasa = 'fonasa'
    isapre = 'isapre'

class PatientBase(BaseModel):
    rut: str = Field(..., description="RUT chileno con guión y dígito verificador")
    nombres: str = Field(..., min_length=2)
    apellidos: str = Field(..., min_length=2)
    fecha_nacimiento: date
    sexo: SexoEnum
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    prevision: PrevisionEnum

    @field_validator('rut')
    @classmethod
    def validar_rut(cls, v):
        if not re.match(r'^[0-9]+-[0-9kK]$', v):
            raise ValueError('Formato de RUT inválido. Debe ser números, un guión y el dígito verificador.')
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    nombres: Optional[str] = Field(None, min_length=2)
    apellidos: Optional[str] = Field(None, min_length=2)
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    prevision: Optional[PrevisionEnum] = None

class PatientResponse(PatientBase):
    patient_id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
