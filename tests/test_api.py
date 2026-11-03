def test_health_endpoints(test_environment) -> None:
    client, _ = test_environment
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {
        "status": "ready",
        "dependency": "database_schema",
    }


def test_cashflow_analysis_endpoint(test_environment) -> None:
    client, _ = test_environment
    response = client.post(
        "/api/v1/cashflow/analyze",
        json={
            "currency": "INR",
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "incomes": [{"occurred_on": "2026-11-01", "amount": "50000.00", "category": "salary"}],
            "expenses": [
                {
                    "occurred_on": "2026-11-02",
                    "amount": "10000.00",
                    "category": "rent",
                    "essential": True,
                },
                {
                    "occurred_on": "2026-11-03",
                    "amount": "5000.00",
                    "category": "shopping",
                    "essential": False,
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["income_total"] == "50000.00"
    assert body["expense_total"] == "15000.00"
    assert body["net_cashflow"] == "35000.00"
    assert body["essential_expenses"] == "10000.00"
    assert body["discretionary_expenses"] == "5000.00"
    assert body["savings_rate_percent"] == "70.00"


def test_api_rejects_out_of_period_entry(test_environment) -> None:
    client, _ = test_environment
    response = client.post(
        "/api/v1/cashflow/analyze",
        json={
            "currency": "INR",
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "incomes": [{"occurred_on": "2026-12-01", "amount": "100.00", "category": "salary"}],
            "expenses": [],
        },
    )
    assert response.status_code == 422


def test_api_rejects_unknown_fields(test_environment) -> None:
    client, _ = test_environment
    response = client.post(
        "/api/v1/cashflow/analyze",
        json={
            "currency": "INR",
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "incomes": [],
            "expenses": [],
            "surprise_field": "should-not-be-silently-accepted",
        },
    )
    assert response.status_code == 422


def test_api_normalizes_category_whitespace(test_environment) -> None:
    client, _ = test_environment
    response = client.post(
        "/api/v1/cashflow/analyze",
        json={
            "currency": "INR",
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "incomes": [],
            "expenses": [
                {
                    "occurred_on": "2026-11-03",
                    "amount": "25.00",
                    "category": "  groceries  ",
                    "essential": True,
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["expense_by_category"][0]["category"] == "groceries"


def test_readiness_requires_an_applied_schema_revision(test_environment) -> None:
    from sqlalchemy import text

    client, session_factory = test_environment
    with session_factory() as db:
        db.execute(text("DROP TABLE alembic_version"))
        db.commit()
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "dependency": "database_or_schema"}
