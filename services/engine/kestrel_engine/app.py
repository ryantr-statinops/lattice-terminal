import secrets
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def create_app(token: str | None = None) -> FastAPI:
    app = FastAPI(title="Kestrel Terminal internal engine", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.internal_token = token

    @app.middleware('http')
    async def internal_auth(request: Request, call_next):
        expected = app.state.internal_token
        actual = request.headers.get('authorization', '')
        if not expected or not secrets.compare_digest(actual, 'Bearer ' + expected):
            return JSONResponse({'error': 'unauthorized'}, status_code=401)
        return await call_next(request)

    @app.get("/internal/v1/health")
    def health():
        return {"service": "kestrel-engine", "status": "ok", "mode": "fixture-only"}

    return app
