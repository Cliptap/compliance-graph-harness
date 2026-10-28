"""Security incident register (documentary evidence, no personal data required)."""
from __future__ import annotations

import argparse
from pathlib import Path

from app import db


def register(db_path: Path | str, nature: str, categories: str, subjects: int, measures: str) -> int:
    with db.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO incidents (occurred_at, nature, data_categories, affected_subjects, measures) "
            "VALUES (?, ?, ?, ?, ?)",
            (db.now_iso(), nature, categories, subjects, measures),
        )
        conn.commit()
        return int(cursor.lastrowid)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.incidents")
    parser.add_argument("--db", type=Path, default=db.default_db_path())
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--nature", default="")
    parser.add_argument("--categories", default="")
    parser.add_argument("--subjects", type=int, default=0)
    parser.add_argument("--measures", default="")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.register:
        incident_id = register(args.db, args.nature, args.categories, args.subjects, args.measures)
        print(f"incident={incident_id}")
    if args.list:
        with db.connect(args.db) as conn:
            for row in conn.execute("SELECT id, occurred_at, nature FROM incidents ORDER BY id").fetchall():
                print(f"{row['id']} | {row['occurred_at']} | {row['nature']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
