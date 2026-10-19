"""Read-only fixture API. No credentials or external clients."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import (
    Article, Candle, ErrorResponse, Health, HealthResponse, Instrument,
    Meta, ArticlesResponse, CandlesResponse, HoldingsResponse,
    InstrumentsResponse, Holding,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "data" / "fixtures"


class FixtureUnavailable(Exception):
    pass


def load_fixture(directory: Path, name: str):
    import json
    from app.schemas import MarketFixture, NewsFixture
    model = MarketFixture if name == "market.json" else NewsFixture if name == "news.json" else None
    try:
        raw = json.loads((directory / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FixtureUnavailable() from exc
    if model is not None:
        try:
            model.model_validate(raw)
        except Exception as exc:
            raise FixtureUnavailable() from exc
    return raw


def error_response(status: int, code: str, message: str):
    return JSONResponse(status_code=status, content={
        "error": {"code": code, "message": message},
        "meta": {"is_synthetic": True},
    })


def create_app(fixture_root: Path | None = None) -> FastAPI:
    directory = fixture_root if fixture_root is not None else FIXTURE_ROOT
    application = FastAPI(title="Kestrel Terminal API", version="0.2.0",
                          responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
                                     500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return error_response(500, "internal_error", "Unexpected server error.")

    @application.exception_handler(FixtureUnavailable)
    async def fixture_error(request: Request, exc: FixtureUnavailable):
        return error_response(503, "fixture_unavailable", "Synthetic fixture is missing or invalid.")

    @application.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return error_response(exc.status_code, "http_error", str(exc.detail))

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return error_response(422, "invalid_request", "Request validation failed.")

    @application.get("/api/v1/health", response_model=HealthResponse)
    def health():
        return HealthResponse(data=Health(), meta=Meta())

    @application.get("/api/v1/market/instruments", response_model=InstrumentsResponse)
    def market_instruments():
        try:
            raw = load_fixture(directory, "market.json")
        except FixtureUnavailable:
            raise
        instruments = [Instrument(**item) for item in raw.get("instruments", [])]
        return InstrumentsResponse(data=instruments, meta=Meta())

    @application.get("/api/v1/market/candles", response_model=CandlesResponse)
    def market_candles(
        instrument_id: str = Query(...),
        interval: str = Query(...),
    ):
        try:
            raw = load_fixture(directory, "market.json")
        except FixtureUnavailable:
            raise
        candles = []
        for item in raw.get("candles", []):
            if item.get("instrument_id") != instrument_id:
                continue
            if item.get("interval") != interval:
                continue
            candles.append(Candle(**item))
        if not any(i.get("instrument_id") == instrument_id for i in raw.get("instruments", [])):
            raise HTTPException(status_code=404, detail="instrument not found")
        return CandlesResponse(data=candles, meta=Meta())

    @application.get("/api/v1/news/articles", response_model=ArticlesResponse)
    def news_articles(instrument_id: str | None = Query(default=None)):
        try:
            raw = load_fixture(directory, "news.json")
        except FixtureUnavailable:
            raise
        articles = [Article(**item) for item in raw.get("articles", [])]
        if instrument_id is not None:
            articles = [a for a in articles if instrument_id in a.instrument_ids]
        return ArticlesResponse(data=articles, meta=Meta())

    @application.get("/api/v1/portfolio/holdings", response_model=HoldingsResponse)
    def portfolio_holdings():
        return HoldingsResponse(data=[], meta=Meta())

    return application

app = create_app()
