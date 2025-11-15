import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.features.reviews.infrastructure.fastapi.router import reviews_router
from app.shared.infrastructure.database import close_connection_pool, open_connection_pool
from app.shared.infrastructure.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):  # noqa: ANN201
    open_connection_pool()
    try:
        yield
    finally:
        close_connection_pool()


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.debug,
    openapi_url=settings.app.openapi_url,
    lifespan=lifespan,
)

app.include_router(reviews_router, prefix=settings.app.api_prefix)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def main() -> None:
    config = uvicorn.Config("main:app", port=settings.app.port, log_level=settings.log_level)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
