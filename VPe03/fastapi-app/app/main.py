from fastapi import FastAPI
from app.routers import health, datetime, welcome

app = FastAPI(title="Test FastAPI App", version="1.0.0")

app.include_router(health.router)
app.include_router(datetime.router)
app.include_router(welcome.router)