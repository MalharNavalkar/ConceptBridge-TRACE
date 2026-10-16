"""Import the previous single-user SQLite records into one pre-existing account.

Run only after the app is migrated and the destination student is registered:
  python scripts/import_legacy_sqlite.py --source conceptbridge.db --email learner@example.com
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.models import Activity, LessonProgress, Project, QuizAttempt, Task, User

def parse_time(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed=datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Path to the preserved previous conceptbridge.db file")
    parser.add_argument("--email", required=True, help="Exact registered account that will own imported records")
    args=parser.parse_args()
    source=sqlite3.connect(args.source)
    source.row_factory=sqlite3.Row
    init_db()
    with SessionLocal.begin() as target:
        user=target.scalar(select(User).where(User.email==args.email.strip().lower()))
        if not user:
            raise SystemExit("Destination account not found. Register the student first; no data was imported.")
        lessons=source.execute("SELECT slug,opened_at,completed_at FROM lessons").fetchall()
        activities=source.execute("SELECT kind,detail,created_at FROM activities ORDER BY id").fetchall()
        attempts=source.execute("SELECT score,total,details,created_at FROM quiz_attempts ORDER BY id").fetchall()
        projects=source.execute("SELECT id,title,description,created_at FROM projects ORDER BY id").fetchall()
        tasks=source.execute("SELECT project_id,title,kind,done,created_at FROM tasks ORDER BY id").fetchall()
        for old in lessons:
            current=target.scalar(select(LessonProgress).where(LessonProgress.user_id==user.id,LessonProgress.lesson_slug==old["slug"]))
            if not current:
                target.add(LessonProgress(user_id=user.id,lesson_slug=old["slug"],opened_at=parse_time(old["opened_at"]),completed_at=parse_time(old["completed_at"])))
        for row in activities:
            target.add(Activity(user_id=user.id,kind=row["kind"],detail=row["detail"],created_at=parse_time(row["created_at"]) or datetime.now(timezone.utc)))
        for row in attempts:
            details=json.loads(row["details"])
            target.add(QuizAttempt(user_id=user.id,score=row["score"],total=row["total"],details=json.dumps(details),created_at=parse_time(row["created_at"]) or datetime.now(timezone.utc)))
        project_map={}
        for row in projects:
            project=Project(owner_user_id=user.id,title=row["title"],description=row["description"] or "",created_at=parse_time(row["created_at"]) or datetime.now(timezone.utc))
            target.add(project); target.flush(); project_map[row["id"]]=project.id
        for row in tasks:
            project_id=project_map.get(row["project_id"])
            if project_id:
                target.add(Task(project_id=project_id,title=row["title"],kind=row["kind"] or "task",done=bool(row["done"]),created_at=parse_time(row["created_at"]) or datetime.now(timezone.utc)))
    source.close()
    print(f"Imported {len(lessons)} lesson records, {len(attempts)} quiz attempts, {len(projects)} projects, {len(tasks)} tasks, and {len(activities)} activities for {args.email.strip().lower()}.")
    print("Re-run only if duplicate imports are intended; this tool does not deduplicate quiz/activity/project history.")

if __name__=="__main__": main()
