from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from flowpilot.api.routes import router
from flowpilot.config import get_settings

SESSION_MAX_AGE = 12 * 60 * 60  # 12 saat


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FlowPilot")
    # İmzalı çerezde yalnızca kullanıcı kimliği tutulur.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="flowpilot_session",
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.env == "production",
    )
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.env}

    return app


app = create_app()
