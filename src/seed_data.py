"""Seed con timestamps variados — simula un dia de consultorio con auditoria"""
import asyncio, httpx, time
from datetime import datetime, timedelta, timezone

API = "http://localhost:8000/api/v1"
TOKEN = None
RECEP_TOKEN = None


async def login(client, email, password):
    res = await client.post("http://localhost:8000/token", data={"username": email, "password": password})
    return res.json()["access_token"]


async def seed():
    global TOKEN, RECEP_TOKEN
    async with httpx.AsyncClient(timeout=30) as client:
        TOKEN = await login(client, "admin@clinic.com", "admin123")
        RECEP_TOKEN = await login(client, "recepcionista@clinic.com", "admin123")

        h = lambda: {"Authorization": f"Bearer {TOKEN}"}
        rh = lambda: {"Authorization": f"Bearer {RECEP_TOKEN}"}

        # Limpiar todo
        print("[*] Limpiando datos anteriores...")
        await client.request("DELETE", f"{API}/audit", content='{"confirm":"delete"}', headers={**h(), "Content-Type": "application/json"})
        # Eliminar entidades existentes
        for pid in ["pat-01","pat-02","pat-03","pat-04","pat-05"]:
            try: await client.delete(f"{API}/patients/{pid}", headers=h())
            except: pass
        for did in ["doc-1","doc-2","doc-3","doc-4"]:
            try: await client.delete(f"{API}/practitioners/{did}", headers=h())
            except: pass
        for aid in [f"apt-{i:02d}" for i in range(1,20)]:
            try: await client.delete(f"{API}/appointments/{aid}", headers=h())
            except: pass
        await asyncio.sleep(0.5)
        print("  Datos limpios.")

        # Practitioners
        doctors = [
            ("doc-1", "11111111-1", "Dra. Maria Gonzalez", "Medicina General"),
            ("doc-2", "22222222-2", "Dr. Pedro Silva", "Pediatria"),
            ("doc-3", "33333333-3", "Dra. Carmen Munoz", "Cardiologia"),
        ]
        for did, rid, name, spec in doctors:
            await client.post(f"{API}/practitioners/", json={"id": did, "identifier": rid, "name": name, "specialty": spec}, headers=h())
            print(f"  + Medico: {name}")

        # Patients
        patients = [
            ("pat-01", "15123456-7", "Juan Perez"),
            ("pat-02", "16234567-8", "Ana Soto"),
            ("pat-03", "17345678-9", "Luis Rojas"),
            ("pat-04", "18456789-0", "Elena Diaz"),
            ("pat-05", "19567890-1", "Martin Castro"),
        ]
        for pid, rid, name in patients:
            await client.post(f"{API}/patients/", json={"id": pid, "identifier": rid, "name": name}, headers=h())
            print(f"  + Paciente: {name}")

        print("\n[*] Registrando citas en diferentes horarios...")
        base = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)

        # Cada cita con timestamp distinto
        appointments = [
            ("pat-01", "doc-1", 9, 0, h()),     # 09:00 - admin
            ("pat-02", "doc-2", 9, 30, rh()),    # 09:30 - recepcionista
            ("pat-03", "doc-1", 10, 0, h()),     # 10:00 - admin
            ("pat-04", "doc-3", 10, 30, rh()),   # 10:30 - recepcionista
            ("pat-05", "doc-2", 11, 0, h()),     # 11:00 - admin
            ("pat-01", "doc-3", 14, 0, rh()),    # 14:00 - recepcionista (tarde)
            ("pat-03", "doc-2", 15, 30, h()),    # 15:30 - admin
        ]

        for i, (pat_id, doc_id, hour, minute, auth_headers) in enumerate(appointments):
            start = base.replace(hour=hour, minute=minute)
            end = start + timedelta(minutes=30)
            payload = {
                "id": f"apt-{i+1:02d}",
                "status": "agendada",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "patient_id": pat_id,
                "practitioner_id": doc_id,
            }
            who = "admin" if auth_headers == h() else "recepcionista"
            res = await client.post(f"{API}/appointments/", json=payload, headers=auth_headers)
            if res.status_code in (200, 201):
                print(f"  + Cita {start.strftime('%H:%M')} — {who}")
            await asyncio.sleep(0.2)  # timestamps diferentes

        # UPDATE: recepcionista modifica nombre (via recrear con mismo ID)
        print("\n[*] Operaciones de modificacion...")
        await asyncio.sleep(0.3)
        # Para simular UPDATE: eliminamos y recreamos con datos cambiados
        await client.delete(f"{API}/patients/pat-02", headers=h())
        await asyncio.sleep(0.2)
        await client.post(f"{API}/patients/", json={"id": "pat-02", "identifier": "16234567-8", "name": "Ana Soto Actualizada"}, headers=rh())
        print(f"  ~ UPDATE paciente pat-02 (recepcionista)")

        await asyncio.sleep(0.3)
        # Cambiar estado de cita a confirmada
        await client.delete(f"{API}/appointments/apt-01", headers=h())
        await asyncio.sleep(0.2)
        await client.post(f"{API}/appointments/", json={"id": "apt-01", "status": "confirmada", "start_time": base.replace(hour=9, minute=0).isoformat(), "end_time": base.replace(hour=9, minute=30).isoformat(), "patient_id": "pat-01", "practitioner_id": "doc-1"}, headers=h())
        print(f"  ~ UPDATE cita apt-01: confirmada (admin)")

        # DELETE: admin elimina una cita
        await client.delete(f"{API}/appointments/apt-02", headers=h())
        print(f"  ~ DELETE cita apt-02 (admin)")

        await asyncio.sleep(0.3)
        # DELETE: recepcionista elimina paciente
        await client.delete(f"{API}/patients/pat-05", headers=rh())
        print(f"  ~ DELETE paciente pat-05 (recepcionista)")

        # Verificar
        res = await client.get(f"{API}/audit?limit=5", headers=h())
        total = res.json()["meta"]["total"]
        print(f"\n[OK] Total eventos de auditoria: {total}")
        print("[OK] Refresca el frontend. La vista de auditoria ahora muestra eventos agrupados.")


if __name__ == "__main__":
    asyncio.run(seed())
