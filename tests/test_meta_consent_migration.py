from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    text,
)
from sqlalchemy.exc import IntegrityError

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "7a05f3c2d9b1_ai_assistance_consent.py"
)
SPEC = importlib.util.spec_from_file_location("ai_assistance_consent_migration", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


def test_consent_constraint_upgrade_and_downgrade_are_safe():
    engine = create_engine("sqlite+pysqlite://")
    metadata = MetaData()
    table = Table(
        "consent_grants",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("purpose", String(64), nullable=False),
        CheckConstraint(
            "purpose IN ('household_sharing', 'commons_aggregation', 'opportunity_matching', "
            "'benefits_discovery', 'partner_offer_personalization', 'research_participation', "
            "'support_case_processing', 'economic_defence', 'enterprise_assistance')",
            name="ck_consent_purpose",
        ),
    )
    metadata.create_all(engine)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            MIGRATION.upgrade()

        connection.execute(insert(table).values(purpose="ai_assistance"))
        connection.commit()
        with Operations.context(context), pytest.raises(RuntimeError, match="consent grants exist"):
            MIGRATION.downgrade()

        connection.execute(text("DELETE FROM consent_grants WHERE purpose = 'ai_assistance'"))
        connection.commit()
        with Operations.context(context):
            MIGRATION.downgrade()

        with pytest.raises(IntegrityError):
            connection.execute(insert(table).values(purpose="ai_assistance"))
        connection.rollback()
    engine.dispose()
