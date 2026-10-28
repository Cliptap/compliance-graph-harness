"""Retention purge: anonymise customers whose retention period expired."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import db


def purge_expired(db_path: Path | str, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    purged = 0
    with db.connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM customers").fetchall()
        for row in rows:
            created = datetime.fromisoformat(row["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created + timedelta(days=row["retention_days"]) > now:
                continue
            conn.execute(
                "UPDATE customers SET email = ?, rut = NULL, phone = NULL, full_name = 'Anonimizado', "
                "password_hash = '!', blocked = 0, marketing_opt_in = 0, updated_at = ? WHERE id = ?",
                (f"anon-{row['id']}@invalid", db.now_iso(), row["id"]),
            )
            conn.execute("DELETE FROM addresses WHERE customer_id = ?", (row["id"],))
            conn.execute("UPDATE consents SET withdrawn_at = ? WHERE customer_id = ? AND withdrawn_at IS NULL",
                         (db.now_iso(), row["id"]))
            purged += 1
        conn.commit()
    return purged


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.retention")
    parser.add_argument("--db", type=Path, default=db.default_db_path())
    parser.add_argument("--purge", action="store_true")
    args = parser.parse_args()
    if args.purge:
        print(f"anonymised={purge_expired(args.db)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
