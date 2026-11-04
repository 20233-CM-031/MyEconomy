"""Add purpose-bound consent for minimized Meta model assistance.

Revision ID: 7a05f3c2d9b1
Revises: c1d4e7a9f204
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "7a05f3c2d9b1"
down_revision = "c1d4e7a9f204"
branch_labels = None
depends_on = None

_OLD_PURPOSES = (
    "'household_sharing', 'commons_aggregation', 'opportunity_matching', "
    "'benefits_discovery', 'partner_offer_personalization', 'research_participation', "
    "'support_case_processing', 'economic_defence', 'enterprise_assistance'"
)
_NEW_PURPOSES = _OLD_PURPOSES + ", 'ai_assistance'"


def upgrade() -> None:
    with op.batch_alter_table("consent_grants") as batch_op:
        batch_op.drop_constraint("ck_consent_purpose", type_="check")
        batch_op.create_check_constraint("ck_consent_purpose", f"purpose IN ({_NEW_PURPOSES})")


def downgrade() -> None:
    connection = op.get_bind()
    ai_grant_count = connection.execute(
        text("SELECT COUNT(*) FROM consent_grants WHERE purpose = 'ai_assistance'")
    ).scalar_one()
    if ai_grant_count:
        raise RuntimeError(
            "Cannot downgrade while AI assistance consent grants exist; revoke and remove "
            "them through the approved data-retention process first."
        )
    with op.batch_alter_table("consent_grants") as batch_op:
        batch_op.drop_constraint("ck_consent_purpose", type_="check")
        batch_op.create_check_constraint("ck_consent_purpose", f"purpose IN ({_OLD_PURPOSES})")
