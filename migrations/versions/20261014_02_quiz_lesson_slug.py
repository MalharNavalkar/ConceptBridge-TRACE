"""Associate each stored quiz attempt with its lesson.

Revision ID: 20261014_02
Revises: 20261014_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261014_02"
down_revision = "20261014_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "quiz_attempts",
        sa.Column("lesson_slug", sa.String(length=80), nullable=False, server_default="half-adder"),
    )
    op.create_index("ix_quiz_attempts_lesson_slug", "quiz_attempts", ["lesson_slug"])


def downgrade():
    op.drop_index("ix_quiz_attempts_lesson_slug", table_name="quiz_attempts")
    op.drop_column("quiz_attempts", "lesson_slug")
