"""Application composition root."""

from fastapi import FastAPI

from myeconomy.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="MyEconomy API",
        version="0.1.0",
        description=(
            "Engineering foundation for a personal economic agency and collective "
            "opportunity intelligence platform."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(router)

    @app.get("/health/live", tags=["health"])
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", tags=["health"])
    def readiness() -> dict[str, str]:
        # No external dependencies exist in Iteration 00. This endpoint will
        # gain dependency probes when persistence/queues are introduced.
        return {"status": "ready"}

    return app


app = create_app()
