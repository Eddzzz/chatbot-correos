"""Explicit, local-only data import into an ALREADY PREPARED isolated sandbox.

Does not execute source functions, DDL, ACLs or ownership statements. Never run
against the operational database. Original backup remains unchanged.
PGPASSWORD or a PostgreSQL password file supplies credentials, never CLI secrets.
"""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inspect_backup import find_pg_restore

TABLES = (
    "estados", "eventos", "ventanilla", "sucursales", "origen", "destino", "peso", "servicio",
    "tarifario", "paquetes_certi", "paquetes_ordi", "paquetes_ems", "paquetes_contrato", "paquetes_int",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--user", required=True)
    parser.add_argument("--confirm-local-sensitive-data-import", action="store_true")
    args = parser.parse_args()
    if not args.database.startswith("correos_sandbox_") or not args.database.replace("_", "").isalnum():
        parser.error("Destination must be an isolated correos_sandbox_* database name.")
    if not args.confirm_local_sensitive_data_import:
        parser.error("Explicit confirmation required: selected source tables contain personal data.")
    command = [find_pg_restore(), "--host=127.0.0.1", f"--port={args.port}",
               f"--username={args.user}", f"--dbname={args.database}", "--data-only",
               "--no-owner", "--no-privileges", "--exit-on-error", "--single-transaction",
               "--schema=public"]
    command += [f"--table={table}" for table in TABLES]
    subprocess.run(command + [str(args.backup)], check=True)


if __name__ == "__main__":
    main()
