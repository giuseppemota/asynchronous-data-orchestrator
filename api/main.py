import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.orders import router as orders_router
from shared.config import settings
from shared.database import create_tables

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(title="Order Orchestrator API", lifespan=lifespan)
app.include_router(orders_router)
