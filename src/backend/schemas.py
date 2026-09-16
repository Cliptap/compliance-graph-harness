from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class PatientBase(BaseModel):
    identifier: str = Field(..., description="RUT o NHI del paciente")
    name: str
    birth_date: Optional[datetime] = None

class PatientCreate(PatientBase):
    id: str = Field(..., description="Identificador único FHIR (UUID o prefijo)")

class PatientResponse(PatientBase):
    id: str
    is_deleted: bool
    
    model_config = ConfigDict(from_attributes=True)

class PractitionerBase(BaseModel):
    id: str
    identifier: str
    name: str = Field(..., max_length=150)
    specialty: Optional[str] = None
    telecom: Optional[str] = None
    email: Optional[str] = None

class PractitionerCreate(PractitionerBase):
    generate_credentials: bool = False

class PractitionerUpdate(BaseModel):
    identifier: str
    name: str = Field(..., max_length=150)
    specialty: Optional[str] = None
    telecom: Optional[str] = None

class PractitionerResponse(PractitionerBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    generated_password: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class AppointmentBase(BaseModel):
    id: str
    status: str
    start_time: datetime
    end_time: datetime
    patient_id: str
    practitioner_id: str

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogRead(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    operation: str
    changed_by: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogDelete(BaseModel):
    confirm: str
