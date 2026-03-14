import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.properties import router as properties_router
from app.routes.scraping import router as scraping_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Immobilier Normandie API",
    description="Recherche immobilière Seine-Maritime & Eure",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS_ORIGINS peut contenir plusieurs URLs séparées par des virgules
# Ex: "https://mon-app.vercel.app,http://localhost:5173"
_cors_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties_router)
app.include_router(scraping_router)


@app.get("/")
async def root():
    return {"message": "Immobilier Normandie API", "docs": "/docs"}
