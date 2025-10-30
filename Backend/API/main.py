# FastAPI ana uygulama dosyası
# Bu dosya FastAPI uygulamasının ana giriş noktasıdır

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from SoilType import soil_api as soil_router
from Weather import router as weather_router
from MachineLearning import ml_api as ml_router
import logging



# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI uygulaması oluştur
app = FastAPI(
    title="Aidea API",
    version="1.0.0",
    description="Soil Analysis and Weather API"
)


# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """
    Uygulama başladığında Redis'e bağlan ve cache'i başlat.
    """
    try:
        # Redis bağlantısı (localhost'taki varsayılan porta bağlanır)
        redis_conn = aioredis.from_url("redis://localhost:6379")
        FastAPICache.init(RedisBackend(redis_conn), prefix="aidea-cache")
        logger.info("Redis cache bağlantısı başarıyla kuruldu.")
    except Exception as e:
        logger.error(f"Redis cache'e bağlanırken hata oluştu: {e}")

# Router'ları ekle
app.include_router(soil_router.router)
app.include_router(weather_router.router)
app.include_router(ml_router.router)

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
            "weather": "/weather/",
            "ml_analysis": "/ml/",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    """Sağlık kontrolü"""
    return {"status": "ok", "service": "Aidea API"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )