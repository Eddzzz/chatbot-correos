"""Export only table definitions and foreign keys; never restore archive contents."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess


def find_pg_restore() -> str:
    executable = os.getenv("PG_RESTORE") or shutil.which("pg_restore")
    if executable:
        return executable
    windows = Path("C:/Program Files/PostgreSQL/18/bin/pg_restore.exe")
    if windows.exists():
        return str(windows)
    raise SystemExit("Set PG_RESTORE to a PostgreSQL 18+ pg_restore executable.")


def extract_structure(schema: str) -> str:
    tables = re.findall(r"^CREATE TABLE public\.[\s\S]*?^\);", schema, re.M)
    foreign_keys = re.findall(
        r"^ALTER TABLE ONLY public\.[^\n]+\n\s+ADD CONSTRAINT [^\n]+ FOREIGN KEY[^;]+;",
        schema, re.M,
    )
    if not tables:
        raise ValueError("No table definitions found; output was not written.")
    return "-- Structure only; no rows, functions, ownership or grants. Not a migration.\n\n" + "\n\n".join(tables + foreign_keys) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.backup.open("rb") as source:
        if source.read(5) != b"PGDMP":
            raise SystemExit("Expected a PostgreSQL custom archive.")
    result = subprocess.run(
        [find_pg_restore(), "--schema-only", "--no-owner", "--no-privileges", "--file=-", str(args.backup)],
        capture_output=True, check=True,
    )
    structure = extract_structure(result.stdout.decode("utf-8").replace('\r\n', '\n'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(structure, encoding="utf-8", newline='\n')
    print(f"Saved structure only: {structure.count('CREATE TABLE ')} tables, {structure.count(' FOREIGN KEY ')} foreign keys")


if __name__ == "__main__":
    main()
