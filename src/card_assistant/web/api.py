import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI

from card_assistant.adapters.planners import DemoPlanner, OpenAIPlanner, UnconfiguredPlanner
from card_assistant.application.generate import DraftPlanner, GenerateCard, GenerationError
from card_assistant.config import Settings
from card_assistant.domain.models import Card
from card_assistant.web.presentation import to_markdown
from card_assistant.web.schemas import ProductInput

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]
ERROR_HTTP_STATUS = {
    "provider_timeout": 504,
    "provider_rate_limit": 429,
    "provider_auth": 503,
    "missing_api_key": 503,
}


def create_app(settings: Settings | None = None, planner: DraftPlanner | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = None
        selected = planner
        if selected is None:
            if config.card_mode == "demo":
                selected = DemoPlanner()
            elif config.openai_api_key.get_secret_value():
                # One SDK retry for transient errors; a total deadline also bounds retries.
                client = AsyncOpenAI(
                    api_key=config.openai_api_key.get_secret_value(),
                    timeout=config.llm_timeout_seconds,
                    max_retries=1,
                )
                selected = OpenAIPlanner(
                    client, config.openai_model, config.llm_timeout_seconds + 5
                )
            else:
                selected = UnconfiguredPlanner()
        app.state.generate = GenerateCard(selected)
        try:
            yield
        finally:
            if client:
                await client.close()

    app = FastAPI(title="Карточка — AI-помощник", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(GenerationError)
    async def generation_error(request: Request, exc: GenerationError):
        request_id = uuid4().hex
        # Do not log source documents, tokens, provider exceptions, or API error bodies.
        logger.warning("Card generation failed", extra={"code": exc.code, "request_id": request_id})
        return JSONResponse(
            status_code=ERROR_HTTP_STATUS.get(exc.code, 502),
            content={"error": {"code": exc.code, "message": exc.message, "request_id": request_id}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(s) for s in error["loc"] if s != "body"),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_input",
                    "message": "Проверьте JSON и заполнение полей.",
                    "details": details,
                }
            },
        )

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "mode": config.card_mode,
            "configured": config.card_mode == "demo"
            or bool(config.openai_api_key.get_secret_value()),
        }

    @app.post("/api/generate")
    async def generate(product: ProductInput, request: Request):
        card: Card = await request.app.state.generate.execute(product.to_domain())
        return {
            "card": asdict(card),
            "markdown": to_markdown(card),
            "meta": {
                "mode": config.card_mode,
                "llm_called": config.card_mode == "live",
                "model": config.openai_model if config.card_mode == "live" else None,
                "title_length": len(card.seo_title),
                "description_length": len(card.seo_description),
                "needs_review": True,
                "prompt_version": "grounded-plan-v1",
            },
        }

    dist = ROOT / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        async def index():
            return FileResponse(dist / "index.html")

        @app.get("/favicon.svg", include_in_schema=False)
        async def favicon():
            return FileResponse(dist / "favicon.svg", media_type="image/svg+xml")
    else:

        @app.get("/", include_in_schema=False)
        async def build_hint():
            return {
                "message": "Соберите интерфейс: cd frontend; npm ci; npm run build. "
                "API доступно по /docs."
            }

    return app
