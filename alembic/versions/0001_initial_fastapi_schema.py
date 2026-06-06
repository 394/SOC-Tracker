from alembic import op
import sqlalchemy as sa


revision = "0001_initial_fastapi_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fastapi_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=220), nullable=False),
        sa.Column("role", sa.String(length=2), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_fastapi_users_username", "fastapi_users", ["username"], unique=True)

    op.create_table(
        "fastapi_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("analyst", sa.String(length=80), nullable=False),
        sa.Column("tactic", sa.String(length=100), nullable=False),
        sa.Column("asset", sa.String(length=160), nullable=False),
        sa.Column("iocs_json", sa.Text(), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("assigned_by_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("escalated_by_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_fastapi_alerts_alert_id", "fastapi_alerts", ["alert_id"], unique=True)

    op.create_table(
        "fastapi_alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("fastapi_alerts.id"), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("assigned_from_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "fastapi_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("fastapi_alerts.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_fastapi_evidence_stored_name", "fastapi_evidence", ["stored_name"], unique=True)

    op.create_table(
        "fastapi_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("fastapi_users.id"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_ip", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("fastapi_audit_logs")
    op.drop_index("ix_fastapi_evidence_stored_name", table_name="fastapi_evidence")
    op.drop_table("fastapi_evidence")
    op.drop_table("fastapi_alert_events")
    op.drop_index("ix_fastapi_alerts_alert_id", table_name="fastapi_alerts")
    op.drop_table("fastapi_alerts")
    op.drop_index("ix_fastapi_users_username", table_name="fastapi_users")
    op.drop_table("fastapi_users")
