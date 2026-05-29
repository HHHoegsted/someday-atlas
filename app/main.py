from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import create_db_and_tables
from app.routers.api import router as api_router
from app.routers.web import router as web_router


app = FastAPI(title="Someday Atlas")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_router)
app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()