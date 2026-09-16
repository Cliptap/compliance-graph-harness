from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.database import Base
import uuid

class SoftDeleteMixin:
    """Mixin para incluir marcas temporales y banderas de borrado lógico."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Patient(Base, SoftDeleteMixin):
    """Recurso FHIR - Patient"""
    __tablename__ = "patients"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    identifier: Mapped[str] = mapped_column(String, unique=True, index=True) # RUT o NHI
    name: Mapped[str] = mapped_column(String)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Practitioner(Base, SoftDeleteMixin):
    """Recurso FHIR - Practitioner"""
    __tablename__ = "practitioners"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    identifier: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String, nullable=True)
    telecom: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    
class Appointment(Base, SoftDeleteMixin):
    """Recurso FHIR - Appointment"""
    __tablename__ = "appointments"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, default="pending") 
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    practitioner_id: Mapped[str] = mapped_column(ForeignKey("practitioners.id"))
    
    patient = relationship("Patient")
    practitioner = relationship("Practitioner")

class AuditLog(Base):
    """Registro de auditoria — trazabilidad granular por campo"""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
