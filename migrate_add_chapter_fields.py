"""
One-off migration: add chapter_number, unlock_time, requires_previous_completion, panels_json
to existing `contents` table. Safe to run multiple times (skips if column exists).
Run from project root: python migrate_add_chapter_fields.py
"""
import sqlite3
import os

from config import config

def main():
    db_path = config.DB_PATH
    if not os.path.isfile(db_path):
        print("No database found; run the app once to create it.")
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(contents)")
    cols = {row[1] for row in cur.fetchall()}
    add = []
    if "chapter_number" not in cols:
        add.append(("chapter_number", "INTEGER NOT NULL DEFAULT 1"))
    if "unlock_time" not in cols:
        add.append(("unlock_time", "TEXT"))
    if "requires_previous_completion" not in cols:
        add.append(("requires_previous_completion", "INTEGER NOT NULL DEFAULT 0"))
    if "panels_json" not in cols:
        add.append(("panels_json", "TEXT"))
    for name, spec in add:
        cur.execute(f"ALTER TABLE contents ADD COLUMN {name} {spec}")
        print(f"Added column: {name}")
    conn.commit()
    conn.close()
    if not add:
        print("All chapter columns already present.")
    else:
        print("Migration done.")

if __name__ == "__main__":
    main()
