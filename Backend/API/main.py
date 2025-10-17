# FastAPI ana uygulama dosyası
# Bu dosya FastAPI uygulamasının ana giriş noktasıdır

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from SoilType.router import router as soil_router

# FastAPI uygulaması oluştur
app = FastAPI(
    title="Aidea API",
    version="1.0.0",
    description="Soil Analysis, Weather, and ML Prediction API"
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(soil_router, prefix="/soiltype", tags=["Soil Analysis"])

# Ana endpoint'ler
@app.get("/")
def root():
    """Ana sayfa - API bilgileri"""
    return {
        "message": "Aidea API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "soil_analysis": "/soiltype/",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    """Sağlık kontrolü"""
    return {"status": "ok", "service": "Aidea API"}