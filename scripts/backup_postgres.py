"""Create a manual pg_dump backup from DATABASE_URL without putting credentials in argv.

Requires the PostgreSQL client utilities (`pg_dump`). Example:
  python scripts/backup_postgres.py --output-dir /secure/private/backups

The output contains student data; protect and encrypt the destination separately.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlsplit

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",default="backups",help="Private directory for the custom-format dump")
    args=parser.parse_args()
    dsn=os.environ.get("DATABASE_URL","")
    if not dsn.startswith(("postgres://","postgresql://","postgresql+psycopg://")):
        raise SystemExit("Set DATABASE_URL to a managed PostgreSQL URL; SQLite is not backed up by this script.")
    pg_dump=shutil.which("pg_dump")
    if not pg_dump:
        raise SystemExit("pg_dump was not found. Install PostgreSQL client tools, then retry.")
    parsed=urlsplit(dsn)
    if not parsed.hostname or not parsed.path.strip("/"):
        raise SystemExit("DATABASE_URL is missing a PostgreSQL host or database name.")
    target=Path(args.output_dir).expanduser().resolve()
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:
        target.chmod(0o700)
    except OSError:
        pass
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=target/f"conceptbridge-{stamp}.dump"
    env=os.environ.copy()
    env.update({"PGHOST":parsed.hostname,"PGDATABASE":unquote(parsed.path.lstrip("/")),"PGUSER":unquote(parsed.username or ""),"PGPASSWORD":unquote(parsed.password or "")})
    if parsed.port:
        env["PGPORT"]=str(parsed.port)
    for key, values in parse_qs(parsed.query).items():
        if key in {"sslmode","sslrootcert","sslcert","sslkey","application_name","connect_timeout"} and values:
            env["PG"+key.upper()]=unquote(values[-1])
    try:
        subprocess.run([pg_dump,"--format=custom","--no-owner","--no-privileges","--file",str(output)],env=env,check=True)
        try:
            output.chmod(0o600)
        except OSError:
            pass
    except Exception:
        output.unlink(missing_ok=True)
        raise
    print(f"Backup written: {output}")
    print("Move it to encrypted, access-controlled storage. This helper is manual; it does not schedule backups.")

if __name__=="__main__": main()
