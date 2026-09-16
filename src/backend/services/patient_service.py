from datetime import datetime, timedelta
from typing import Optional, List
from ..schemas.patient import PatientCreate, PatientUpdate

# TODO: Reemplazar este diccionario en memoria por conexión a PostgreSQL (Ej: psycopg2, asyncpg, o SQLAlchemy)
# Se utiliza un store en memoria para cumplir la separación de capas y permitir pruebas del endpoint de forma aislada.
_mock_db = {}
_id_counter = 1

class PatientService:
    def list_patients(self, time_filter: str = 'all', sort: str = 'desc') -> List[dict]:
        patients = list(_mock_db.values())
        now = datetime.utcnow()
        
        # Filtro temporal (Simulando la vista SQL: vw_recent_patients_summary)
        filtered = []
        for p in patients:
            p_date = datetime.fromisoformat(p['created_at'])
            if time_filter == 'today':
                if p_date.date() == now.date(): filtered.append(p)
            elif time_filter == 'week':
                if (now - p_date).days <= 7: filtered.append(p)
            elif time_filter == 'month':
                if p_date.month == now.month and p_date.year == now.year: filtered.append(p)
            else:
                filtered.append(p)
                
        # Ordenamiento
        filtered.sort(key=lambda x: x['created_at'], reverse=(sort == 'desc'))
        return filtered

    def get_stats(self, time_filter: str = 'all') -> dict:
        # Simulando la agregación SQL: vw_patient_kpis
        patients = self.list_patients(time_filter)
        total = len(patients)
        fonasa = sum(1 for p in patients if p['prevision'] == 'fonasa')
        isapre = sum(1 for p in patients if p['prevision'] == 'isapre')
        return {"total": total, "fonasa": fonasa, "isapre": isapre}

    def get_patient_by_rut(self, rut: str) -> Optional[dict]:
        return _mock_db.get(rut)

    def create_patient(self, data: PatientCreate) -> dict:
        global _id_counter
        now = datetime.utcnow().isoformat()
        patient_record = data.dict()
        patient_record.update({
            "patient_id": _id_counter,
            "created_at": now,
            "updated_at": now
        })
        _mock_db[data.rut] = patient_record
        _id_counter += 1
        return patient_record

    def update_patient(self, rut: str, data: PatientUpdate) -> Optional[dict]:
        patient = self.get_patient_by_rut(rut)
        if not patient:
            return None
        
        update_data = data.dict(exclude_unset=True)
        if update_data:
            patient.update(update_data)
            patient["updated_at"] = datetime.utcnow().isoformat()
            _mock_db[rut] = patient
            
        return patient

    def delete_patient(self, rut: str) -> bool:
        if rut in _mock_db:
            del _mock_db[rut]
            return True
        return False
