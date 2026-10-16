"""Create accounts, sessions and user-owned learning records.

Revision ID: 20261014_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261014_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_table("login_failures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email_key", sa.String(64), nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_login_failures_email_key", "login_failures", ["email_key"])
    op.create_index("ix_login_failures_failed_at", "login_failures", ["failed_at"])
    op.create_index("ix_login_failures_email_time", "login_failures", ["email_key", "failed_at"])
    op.create_table("lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_slug", sa.String(80), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "lesson_slug", name="uq_lesson_progress_user_slug"))
    op.create_index("ix_lesson_progress_user_id", "lesson_progress", ["user_id"])
    op.create_table("activities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("detail", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_activities_user_id", "activities", ["user_id"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])
    op.create_index("ix_activity_user_time", "activities", ["user_id", "created_at"])
    op.create_table("quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_created_at", "quiz_attempts", ["created_at"])
    op.create_index("ix_attempt_user_time", "quiz_attempts", ["user_id", "created_at"])
    op.create_table("projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_projects_owner_user_id", "projects", ["owner_user_id"])
    op.create_table("tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False, server_default="task"),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])

def downgrade():
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_index("ix_attempt_user_time", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index("ix_activity_user_time", table_name="activities")
    op.drop_table("activities")
    op.drop_table("lesson_progress")
    op.drop_table("login_failures")
    op.drop_table("auth_sessions")
    op.drop_table("users")
