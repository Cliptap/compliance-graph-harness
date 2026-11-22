"""Rights request bookkeeping: mark a request as answered."""
from __future__ import annotations

import argparse
from pathlib import Path

from app import db


def respond(db_path: Path | str, request_id: int, status: str) -> bool:
    with db.connect(db_path) as conn:
        cursor = conn.execute(
            "UPDATE rights_requests SET status = ?, responded_at = ? WHERE id = ?",
            (status, db.now_iso(), request_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.rights")
    parser.add_argument("--db", type=Path, default=db.default_db_path())
    parser.add_argument("--respond", type=int, metavar="ID")
    parser.add_argument("--status", default="answered")
    args = parser.parse_args()
    if args.respond is not None:
        ok = respond(args.db, args.respond, args.status)
        print(f"updated={int(ok)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
