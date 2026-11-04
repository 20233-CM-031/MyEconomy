"""Application composition root."""

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from myeconomy.api.financial_routes import router as financial_router
from myeconomy.api.guardian_routes import router as guardian_router
from myeconomy.api.identity_routes import router as identity_router
from myeconomy.api.personal_power_routes import router as personal_power_router
from myeconomy.api.routes import router as cashflow_router
from myeconomy.domain.errors import ApplicationError
from myeconomy.infrastructure.database import get_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="AwnNORA API",
        version="0.4.0",
        description=(
            "Personal economic agency and collective opportunity intelligence. "
            "Identity, consent, financial data and the Guardian evidence-review "
            "workflow are persisted."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(cashflow_router)
    app.include_router(identity_router)
    app.include_router(financial_router)
    app.include_router(guardian_router)
    app.include_router(personal_power_router)

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_request: Request, exc: ApplicationError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )

    @app.get("/health/live", tags=["health"])
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", tags=["health"], response_model=None)
    def readiness(db: Session = Depends(get_db)) -> JSONResponse | dict[str, str]:
        try:
            db.execute(text("SELECT 1"))
            migrated = db.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one_or_none()
            if migrated is None:
                return JSONResponse(
                    status_code=503,
                    content={"status": "not_ready", "dependency": "database_schema"},
                )
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "dependency": "database_or_schema"},
            )
        return {"status": "ready", "dependency": "database_schema"}

    return app


app = create_app()
