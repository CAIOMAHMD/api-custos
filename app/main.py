from fastapi import FastAPI
from app.routers import custos

app = FastAPI(title="API de Custos Azure")

app.include_router(custos.router)
