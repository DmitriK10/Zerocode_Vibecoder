from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router

app = FastAPI(title="VPk04.1 Triage Service")

app.include_router(router, prefix="/api/v1")


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)