"""Marketing audience: only customers with an active consent and no block."""
from __future__ import annotations

import argparse
from pathlib import Path

from app import db


def active_audience(conn) -> list[int]:
    rows = conn.execute(
        "SELECT c.id FROM customers c "
        "JOIN consents s ON s.customer_id = c.id "
        "WHERE s.purpose = 'marketing' AND s.withdrawn_at IS NULL AND c.blocked = 0 "
        "GROUP BY c.id"
    ).fetchall()
    return [row["id"] for row in rows]


def send_campaign(db_path: Path | str, subject: str) -> int:
    with db.connect(db_path) as conn:
        audience = active_audience(conn)
        for customer_id in audience:
            conn.execute(
                "INSERT INTO marketing_messages (customer_id, subject, sent_at) VALUES (?, ?, ?)",
                (customer_id, subject, db.now_iso()),
            )
        conn.commit()
    return len(audience)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.marketing")
    parser.add_argument("--db", type=Path, default=db.default_db_path())
    parser.add_argument("--audience", action="store_true")
    parser.add_argument("--send", metavar="SUBJECT")
    args = parser.parse_args()
    if args.audience:
        with db.connect(args.db) as conn:
            print(f"audience={len(active_audience(conn))}")
    if args.send:
        print(f"sent={send_campaign(args.db, args.send)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
