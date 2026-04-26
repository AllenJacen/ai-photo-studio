import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import auth, users, uploads, scenes, ai_models, tasks, history, images
from app.api.v1.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Photo Studio API",
    description="AI 生成婚纱照与艺术照平台后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

import re

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _to_camel(key: str) -> str:
    if "_" not in key:
        return key
    parts = key.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _to_snake(key: str) -> str:
    return _CAMEL_RE.sub("_", key).lower()


def _camelize(obj):
    if isinstance(obj, dict):
        return {_to_camel(k): _camelize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_camelize(v) for v in obj]
    return obj


def _snakeize(obj):
    if isinstance(obj, dict):
        return {_to_snake(k): _snakeize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_snakeize(v) for v in obj]
    return obj


class CaseConversionMiddleware(BaseHTTPMiddleware):
    """响应 data 转 camelCase。请求侧由独立的 ASGI 中间件处理(见 SnakeRequestBodyMiddleware)。"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            return response
        if response.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            return response

        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        try:
            payload = json.loads(body_bytes) if body_bytes else None
        except Exception:
            return Response(
                content=body_bytes, status_code=response.status_code,
                headers=dict(response.headers), media_type=response.media_type,
            )

        if isinstance(payload, dict) and {"code", "message", "data"} <= set(payload.keys()):
            wrapped = payload
        elif response.status_code >= 400:
            detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
            wrapped = {"code": response.status_code, "message": detail or "请求失败", "data": None}
        else:
            wrapped = {"code": 0, "message": "ok", "data": payload}

        wrapped["data"] = _camelize(wrapped.get("data"))

        new_body = json.dumps(wrapped, ensure_ascii=False).encode("utf-8")
        new_headers = dict(response.headers)
        new_headers.pop("content-length", None)
        return Response(
            content=new_body,
            status_code=200 if response.status_code < 400 else response.status_code,
            headers=new_headers,
            media_type="application/json",
        )


class SnakeRequestBodyMiddleware:
    """ASGI 中间件: 把 application/json 请求 body 的 camelCase key 转成 snake_case。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/") or scope["method"] not in ("POST", "PUT", "PATCH"):
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers") or [])
        ct = headers.get(b"content-type", b"").decode("latin-1").lower()
        if not ct.startswith("application/json"):
            return await self.app(scope, receive, send)

        body = b""
        more = True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)

        if body:
            try:
                data = json.loads(body)
                body = json.dumps(_snakeize(data)).encode("utf-8")
            except Exception:
                pass

        new_headers = [(k, v) for k, v in scope["headers"] if k != b"content-length"]
        new_headers.append((b"content-length", str(len(body)).encode("latin-1")))
        scope = dict(scope)
        scope["headers"] = new_headers

        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, replay, send)


app.add_middleware(CaseConversionMiddleware)
app.add_middleware(SnakeRequestBodyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误，请稍后重试", "data": None},
    )


def _wrap(router):
    """Wrap router response in standard {code, message, data} format."""
    return router


# Mount routers
PREFIX = "/api/v1"
for router in [auth.router, users.router, uploads.router, scenes.router,
               ai_models.router, tasks.router, history.router, images.router]:
    app.include_router(router, prefix=PREFIX)

app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Photo Studio"}
