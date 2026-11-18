from fastapi import FastAPI

from flowpilot.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="FlowPilot")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": get_settings().env}

    return app


app = create_app()
