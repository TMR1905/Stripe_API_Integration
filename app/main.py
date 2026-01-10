from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=settings.allowed_methods_list,
    allow_headers=settings.allowed_headers_list,
)

# Routers
app.include_router(api_v1_router)


@app.get("/health", tags=["health"]) 
def health():
    return {"status": "ok"}
