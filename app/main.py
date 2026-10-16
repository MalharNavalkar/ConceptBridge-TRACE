from __future__ import annotations
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4
import hmac

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.data.lesson import LESSON
from app.data.quiz import QUESTIONS, score_answers
from app.data.curriculum import BY_SLUG, GROUP_ORDER, LESSONS as CURRICULUM, public_lesson, public_question_list, question_bank
from app.database import SessionLocal, init_db
from app.models import Activity, AuthSession, LessonProgress, LoginFailure, Project, QuizAttempt, Task, User, now_utc
from app.services.auth import digest_token, hash_password, new_csrf_token, new_session_token, verify_password

ROOT = Path(__file__).resolve().parent
SESSION_COOKIE = "cb_session"
CSRF_COOKIE = "cb_csrf"
SESSION_DAYS = 7
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").strip().lower() in {"1", "true", "yes", "on"}
app = FastAPI(title="ConceptBridge-TRACE", version="0.2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

@app.on_event("startup")
def startup():
    init_db()

@app.middleware("http")
async def no_store_api(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").split(",")[0].strip() == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    session = db.get(AuthSession, digest_token(raw))
    if not session or _aware(session.expires_at) <= now_utc():
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    user = db.get(User, session.user_id)
    if not user:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Sign in to continue")
    return user

def require_csrf(request: Request, db: Session, user: User | None = None):
    header = request.headers.get("x-csrf-token", "")
    cookie = request.cookies.get(CSRF_COOKIE, "")
    if not header or not cookie or not hmac.compare_digest(header, cookie):
        raise HTTPException(status_code=403, detail="CSRF verification failed; refresh the page and try again")
    raw_session = request.cookies.get(SESSION_COOKIE)
    if user and raw_session:
        auth = db.get(AuthSession, digest_token(raw_session))
        if not auth or not hmac.compare_digest(auth.csrf_hash, digest_token(header)):
            raise HTTPException(status_code=403, detail="Session CSRF verification failed; refresh the page and try again")

def require_logged_in_csrf(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    require_csrf(request, db, user)

def require_anon_csrf(request: Request):
    require_csrf(request, None)

def set_csrf_cookie(response: Response, token: str):
    response.set_cookie(CSRF_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=False, secure=COOKIE_SECURE, samesite="lax", path="/")

def set_session_cookies(response: Response, token: str, csrf: str):
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/")
    set_csrf_cookie(response, csrf)

def clear_auth_cookies(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=COOKIE_SECURE, httponly=False, samesite="lax")

def issue_session(db: Session, user: User):
    token, csrf = new_session_token(), new_csrf_token()
    db.add(AuthSession(token_hash=digest_token(token), csrf_hash=digest_token(csrf), user_id=user.id,
                       expires_at=now_utc() + timedelta(days=SESSION_DAYS)))
    return token, csrf

def log_activity(db: Session, user_id: str, kind: str, detail: str):
    db.add(Activity(user_id=user_id, kind=kind, detail=detail))

def project_dict(project: Project):
    tasks = [{"id": t.id, "title": t.title, "kind": t.kind, "done": bool(t.done)} for t in project.tasks]
    total = len(tasks)
    complete = sum(1 for t in tasks if t["done"])
    return {"id": project.id, "title": project.title, "description": project.description,
            "created_at": project.created_at, "tasks": tasks, "progress": round(complete / total * 100) if total else 0,
            "completed": complete, "total": total}

def owned_projects(db: Session, user_id: str):
    rows = db.scalars(select(Project).where(Project.owner_user_id == user_id).options(selectinload(Project.tasks)).order_by(Project.id.desc())).all()
    return [project_dict(p) for p in rows]

def progress_summary(db: Session, user_id: str):
    progress_rows = db.scalars(select(LessonProgress).where(LessonProgress.user_id == user_id)).all()
    progress_by_slug = {row.lesson_slug: row for row in progress_rows}
    attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user_id).order_by(QuizAttempt.id.desc())).all()
    activities = db.scalars(select(Activity).where(Activity.user_id == user_id).order_by(Activity.id.desc()).limit(8)).all()
    revision = list(dict.fromkeys(c for a in attempts for c in json.loads(a.details).get("revision_concepts", [])))
    attempts_by_slug = {}
    for attempt in attempts:
        attempts_by_slug.setdefault(attempt.lesson_slug, []).append(attempt)
    lessons = []
    for item in CURRICULUM:
        progress = progress_by_slug.get(item["slug"])
        lesson_attempts = attempts_by_slug.get(item["slug"], [])
        best = max((round(a.score / a.total * 100) for a in lesson_attempts if a.total), default=None)
        lessons.append({"slug":item["slug"], "title":item["modes"]["en"]["title"], "group":item["group"],
                        "difficulty":item["difficulty"], "minutes":item["minutes"], "summary":item["summary"],
                        "opened":bool(progress and progress.opened_at), "completed":bool(progress and progress.completed_at),
                        "attempt_count":len(lesson_attempts), "best_score":best})
    lesson = progress_by_slug.get("half-adder")
    attempts_out = [{"id":a.id, "lesson_slug":a.lesson_slug,
                     "lesson_title":BY_SLUG.get(a.lesson_slug, {}).get("modes", {}).get("en", {}).get("title", "Lesson quiz"),
                     "score":a.score, "total":a.total, "created_at":a.created_at} for a in attempts]
    return {"lesson":{"slug":"half-adder", "title":LESSON["title"], "opened":bool(lesson and lesson.opened_at), "completed":bool(lesson and lesson.completed_at)},
            "lessons":lessons, "lesson_count":len(lessons),
            "lessons_completed":sum(1 for item in lessons if item["completed"]),
            "lessons_opened":sum(1 for item in lessons if item["opened"]),
            "attempts":attempts_out,
            "attempt_count":len(attempts), "correct_answers":sum(a.score for a in attempts),
            "revision_concepts":revision,
            "recent_activity":[{"kind":a.kind,"detail":a.detail,"created_at":a.created_at} for a in activities],
            "projects":owned_projects(db, user_id)}

@app.get("/")
def home():
    return FileResponse(ROOT / "templates" / "index.html")

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    return {"status":"ok", "database":"ready"}

@app.get("/api/auth/csrf")
def get_csrf(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_session = request.cookies.get(SESSION_COOKIE)
    auth = db.get(AuthSession, digest_token(raw_session)) if raw_session else None
    token = request.cookies.get(CSRF_COOKIE, "")
    if auth and token and hmac.compare_digest(auth.csrf_hash, digest_token(token)):
        return {"csrf_token":token}
    token = new_csrf_token()
    if auth:
        auth.csrf_hash = digest_token(token)
        db.commit()
    set_csrf_cookie(response, token)
    return {"csrf_token":token}

@app.get("/api/auth/me")
def auth_me(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    return {"user":{"id":user.id,"email":user.email},"csrf_token":request.cookies.get(CSRF_COOKIE, "")}

class AccountInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

@app.post("/api/auth/register", status_code=201)
def register(payload: AccountInput, request: Request, response: Response, db: Session = Depends(get_db)):
    require_anon_csrf(request)
    exists = db.scalar(select(User.id).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=409, detail="Could not create an account for this email")
    user = User(id=str(uuid4()), email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.flush()
        log_activity(db, user.id, "account_created", "Student account created")
        token, csrf = issue_session(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create an account for this email")
    set_session_cookies(response, token, csrf)
    return {"user":{"id":user.id,"email":user.email},"csrf_token":csrf}

# A precomputed dummy hash keeps unknown-user and wrong-password checks on the same path.
_DUMMY_HASH = hash_password("dummy-account-password-never-used")

@app.post("/api/auth/login")
def login(payload: AccountInput, request: Request, response: Response, db: Session = Depends(get_db)):
    require_anon_csrf(request)
    now = now_utc()
    window = now - timedelta(minutes=15)
    email_key = digest_token(payload.email)
    db.execute(delete(LoginFailure).where(LoginFailure.failed_at < window))
    failures = db.scalar(select(func.count(LoginFailure.id)).where(LoginFailure.email_key == email_key, LoginFailure.failed_at >= window)) or 0
    if failures >= 10:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again in 15 minutes.")
    user = db.scalar(select(User).where(User.email == payload.email))
    valid = verify_password(payload.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not valid:
        db.add(LoginFailure(email_key=email_key))
        db.commit()
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    db.execute(delete(LoginFailure).where(LoginFailure.email_key == email_key))
    token, csrf = issue_session(db, user)
    log_activity(db, user.id, "login", "Signed in")
    db.commit()
    set_session_cookies(response, token, csrf)
    return {"user":{"id":user.id,"email":user.email},"csrf_token":csrf}

@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)):
    require_csrf(request, db, user)
    raw = request.cookies.get(SESSION_COOKIE, "")
    auth = db.get(AuthSession, digest_token(raw))
    if auth:
        db.delete(auth)
        log_activity(db, user.id, "logout", "Signed out")
        db.commit()
    clear_auth_cookies(response)
    response.status_code = 204
    return response

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return progress_summary(db, user.id)

@app.get("/api/lessons")
def lesson_catalog(db: Session = Depends(get_db), user: User = Depends(current_user)):
    summary = progress_summary(db, user.id)
    return {"groups":list(GROUP_ORDER), "lessons":summary["lessons"],
            "lesson_count":summary["lesson_count"], "lessons_completed":summary["lessons_completed"]}

@app.get("/api/lessons/{slug}")
def lesson_detail(slug: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = public_lesson(slug)
    if item is None:
        raise HTTPException(404, "Lesson not found")
    progress = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_slug == slug))
    item.update({"opened":bool(progress and progress.opened_at), "completed":bool(progress and progress.completed_at)})
    return item

@app.post("/api/lessons/{slug}/open")
def open_curriculum_lesson(slug: str, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    item = BY_SLUG.get(slug)
    if item is None:
        raise HTTPException(404, "Lesson not found")
    now = now_utc()
    entry = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_slug == slug))
    if entry:
        first_open = entry.opened_at is None
        entry.opened_at = entry.opened_at or now
    else:
        first_open = True
        db.add(LessonProgress(user_id=user.id, lesson_slug=slug, opened_at=now))
    if first_open:
        log_activity(db, user.id, "lesson_opened", f"{item['modes']['en']['title']} lesson opened")
    db.commit()
    return {"ok":True, "slug":slug}

@app.post("/api/lessons/{slug}/complete")
def complete_curriculum_lesson(slug: str, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    item = BY_SLUG.get(slug)
    if item is None:
        raise HTTPException(404, "Lesson not found")
    now = now_utc()
    entry = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_slug == slug))
    if not entry:
        entry = LessonProgress(user_id=user.id, lesson_slug=slug, opened_at=now)
        db.add(entry)
    entry.opened_at = entry.opened_at or now
    first_complete = entry.completed_at is None
    entry.completed_at = entry.completed_at or now
    if first_complete:
        log_activity(db, user.id, "lesson_completed", f"{item['modes']['en']['title']} lesson completed")
    db.commit()
    return {"ok":True, "slug":slug, "completed":True}

@app.get("/api/lesson")
def lesson():
    return LESSON

@app.post("/api/lesson/open")
def open_lesson(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    now = now_utc()
    entry = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_slug == "half-adder"))
    if entry:
        entry.opened_at = entry.opened_at or now
    else:
        db.add(LessonProgress(user_id=user.id, lesson_slug="half-adder", opened_at=now))
    log_activity(db, user.id, "lesson_opened", "Half Adder lesson opened")
    db.commit()
    return {"ok":True}

@app.post("/api/lesson/complete")
def complete_lesson(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    now = now_utc()
    entry = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_slug == "half-adder"))
    if not entry:
        entry = LessonProgress(user_id=user.id, lesson_slug="half-adder", opened_at=now)
        db.add(entry)
    entry.completed_at = entry.completed_at or now
    log_activity(db, user.id, "lesson_completed", "Half Adder marked complete")
    db.commit()
    return {"ok":True}

@app.get("/api/quiz")
def quiz(lesson_slug: str | None = None, locale: Literal["en","hi","hinglish"] = "en"):
    slug = lesson_slug or "half-adder"
    questions = public_question_list(slug, locale)
    if questions is None:
        raise HTTPException(404, "Lesson not found")
    if lesson_slug is None and locale == "en":
        return questions
    return {"lesson_slug":slug, "lesson_title":BY_SLUG[slug]["modes"][locale]["title"],
            "locale":locale, "questions":questions}

class Answer(BaseModel):
    question_id: str = Field(min_length=2, max_length=20)
    answer: int = Field(ge=0, le=10)
class Attempt(BaseModel):
    answers: list[Answer] = Field(min_length=1, max_length=8)
    lesson_slug: str = Field(default="half-adder", min_length=2, max_length=80)
    locale: Literal["en","hi","hinglish"] = "en"

@app.post("/api/quiz/attempt")
def submit_quiz(payload: Attempt, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    lesson = BY_SLUG.get(payload.lesson_slug)
    questions = question_bank(payload.lesson_slug, payload.locale)
    if lesson is None or questions is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if len(payload.answers) != len(questions) or len({a.question_id for a in payload.answers}) != len(questions):
        raise HTTPException(status_code=422, detail=f"Submit each of this lesson's {len(questions)} quiz questions exactly once")
    try:
        result = score_answers([a.model_dump() for a in payload.answers], questions=questions)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result.update({"lesson_slug":payload.lesson_slug, "lesson_title":lesson["modes"][payload.locale]["title"], "locale":payload.locale})
    db.add(QuizAttempt(user_id=user.id, lesson_slug=payload.lesson_slug, score=result["score"], total=result["total"], details=json.dumps(result, ensure_ascii=False)))
    log_activity(db, user.id, "quiz_attempt", f"{lesson['modes']['en']['title']} quiz: {result['score']}/{result['total']}")
    db.commit()
    return result

class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    kind: Literal["task", "milestone", "checklist"] = "task"
class TaskUpdate(BaseModel):
    done: bool

@app.get("/api/projects")
def projects(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return owned_projects(db, user.id)

@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    title = payload.title.strip()
    if not title:
        raise HTTPException(422, "Project title cannot be blank")
    project = Project(owner_user_id=user.id, title=title, description=payload.description.strip())
    db.add(project)
    db.flush()
    log_activity(db, user.id, "project_created", f"Project created: {title}")
    db.commit()
    db.refresh(project)
    return project_dict(project)

@app.post("/api/projects/{project_id}/tasks", status_code=201)
def create_task(project_id: int, payload: TaskCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    title = payload.title.strip()
    if not title:
        raise HTTPException(422, "Task title cannot be blank")
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_user_id == user.id))
    if not project:
        raise HTTPException(404, "Project not found")
    task = Task(project_id=project_id, title=title, kind=payload.kind, done=False)
    db.add(task)
    log_activity(db, user.id, "task_added", f"Task added: {title}")
    db.commit()
    db.refresh(task)
    return {"id":task.id,"title":task.title,"kind":task.kind,"done":task.done}

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    task = db.scalar(select(Task).join(Project).where(Task.id == task_id, Project.owner_user_id == user.id))
    if not task:
        raise HTTPException(404, "Task not found")
    task.done = payload.done
    log_activity(db, user.id, "task_completed" if payload.done else "task_reopened", f"Task {'completed' if payload.done else 'reopened'}: {task.title}")
    db.commit()
    return {"id":task.id,"title":task.title,"kind":task.kind,"done":task.done}

@app.get("/api/projects/template")
def project_template():
    return {"label":"Example template — Digital Logic Learning Project", "title":"Build and test a logic-gate demo", "description":"A starter plan for learning, building, and documenting a basic digital logic demonstration.", "tasks":[
        {"title":"Review binary addition and half-adder truth table","kind":"task"},
        {"title":"Build an XOR + AND half-adder demonstration","kind":"milestone"},
        {"title":"Test all four input combinations","kind":"checklist"},
        {"title":"Document circuit behavior and observations","kind":"checklist"}
    ]}

@app.post("/api/projects/from-template", status_code=201)
def create_from_template(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_logged_in_csrf)):
    template = project_template()
    project = Project(owner_user_id=user.id, title=template["title"], description=template["description"], tasks=[Task(title=t["title"],kind=t["kind"],done=False) for t in template["tasks"]])
    db.add(project)
    db.flush()
    log_activity(db, user.id, "project_created", "Example digital logic project created from template")
    db.commit()
    return project_dict(project)
