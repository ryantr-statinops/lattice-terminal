from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Kestrel Terminal internal engine", version="1.0.0")

    @app.get("/internal/v1/health")
    def health():
        return {"service": "kestrel-engine", "status": "ok", "mode": "fixture-only"}

    return app
