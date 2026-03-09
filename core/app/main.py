import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .config import settings
from .coverity_client import CoverityClient
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.coverity_client = CoverityClient()
    try:
        yield
    finally:
        await app.state.coverity_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Coverity Assistant Core",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()


def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.core_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
