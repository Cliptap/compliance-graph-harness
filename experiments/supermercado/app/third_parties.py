"""Third-party inventory maintenance."""
from __future__ import annotations

import argparse
from pathlib import Path

from app import db


def add(db_path: Path | str, name: str, purpose: str, region: str) -> int:
    with db.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO third_parties (name, purpose, region) VALUES (?, ?, ?)", (name, purpose, region)
        )
        conn.commit()
        return int(cursor.lastrowid)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.third_parties")
    parser.add_argument("--db", type=Path, default=db.default_db_path())
    parser.add_argument("--add", action="store_true")
    parser.add_argument("--name", default="")
    parser.add_argument("--purpose", default="")
    parser.add_argument("--region", default="")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.add:
        print(f"third_party={add(args.db, args.name, args.purpose, args.region)}")
    if args.list:
        with db.connect(args.db) as conn:
            for row in conn.execute("SELECT * FROM third_parties ORDER BY name").fetchall():
                print(f"{row['name']} | {row['purpose']} | {row['region']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
