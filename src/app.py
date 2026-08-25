from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.exceptions_handler import register_exception_handlers
from routers import admin_router, membership_router, user_router
from services import connect_to_mongodb, disconnect_from_mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongodb()
    yield
    disconnect_from_mongodb()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router=admin_router)
app.include_router(router=membership_router)
app.include_router(router=user_router)


@app.get("/")
def read_root():
    """Returns Hello World."""
    return {"Hello": "World! :,)"}
