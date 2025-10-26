import os
import json
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zekai Masnu Crop Recommendation API",
    description="Akıllı mahsul öneri sistemi - Makine Öğrenmesi API",
    version="1.0.0"
)

# ✅ DINAMIK DOSYA YOLLARI
# API'nin bulunduğu dizin
API_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"API dizini: {API_DIR}")

# Model dosyalarının bulunduğu dizin (bir üst seviye -> Code -> model_outputs)
ML_CODE_DIR = os.path.join(API_DIR, "..", "Code")
MODEL_OUTPUTS_DIR = os.path.join(ML_CODE_DIR, "model_outputs")

# Model dosyasını bulma (pattern matching)
def find_model_file():
    """Model_outputs içindeki en son best_model dosyasını bulur"""
    try:
        if not os.path.exists(MODEL_OUTPUTS_DIR):
            raise FileNotFoundError(f"Model outputs dizini bulunamadı: {MODEL_OUTPUTS_DIR}")
        
        # Tüm .pkl dosyalarını listele
        pkl_files = [f for f in os.listdir(MODEL_OUTPUTS_DIR) if f.endswith('.pkl') and 'best_model' in f]
        
        if not pkl_files:
            raise FileNotFoundError("Best model .pkl dosyası bulunamadı")
        
        # En son dosyayı seç (tarihe göre sırala)
        latest_model = sorted(pkl_files)[-1]
        model_path = os.path.join(MODEL_OUTPUTS_DIR, latest_model)
        logger.info(f"Model dosyası bulundu: {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"Model dosyası bulunamadı: {e}")
        raise

# Summary JSON dosyasını bulma
def find_summary_file():
    """En son summary.json dosyasını bulur"""
    try:
        json_files = [f for f in os.listdir(MODEL_OUTPUTS_DIR) if f.startswith('summary_') and f.endswith('.json')]
        
        if not json_files:
            raise FileNotFoundError("Summary JSON dosyası bulunamadı")
        
        latest_json = sorted(json_files)[-1]
        json_path = os.path.join(MODEL_OUTPUTS_DIR, latest_json)
        logger.info(f"Summary dosyası bulundu: {json_path}")
        return json_path
        
    except Exception as e:
        logger.error(f"Summary dosyası bulunamadı: {e}")
        raise

# ✅ MODEL VE METADATA YÜKLEME
try:
    MODEL_PATH = find_model_file()
    SUMMARY_PATH = find_summary_file()
    
    # Modeli yükle
    model = joblib.load(MODEL_PATH)
    logger.info("✅ Model başarıyla yüklendi")
    
    # Metadata'yı yükle
    with open(SUMMARY_PATH, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    logger.info("✅ Metadata başarıyla yüklendi")
    
    # Feature isimlerini kontrol et
    expected_features = metadata.get("feature_names", [])
    logger.info(f"🔄 Beklenen özellikler: {expected_features}")
    
except Exception as e:
    logger.error(f"❌ Model yükleme hatası: {e}")
    model = None
    metadata = {}

# ✅ PYDANTIC MODELLERI
class SoilFeatures(BaseModel):
    """Toprak ve iklim özellikleri için model"""
    n: float  # Nitrogen
    p: float  # Phosphorus
    k: float  # Potassium
    temperature: float  # Sıcaklık (°C)
    humidity: float     # Nem (%)
    ph: float          # Toprak pH
    rainfall: float    # Yağış (mm)

class PredictionResponse(BaseModel):
    """Tahmin cevabı modeli"""
    recommended_crop: str
    confidence: str
    model_used: str
    features_used: List[str]
    all_probabilities: Optional[dict] = None

class HealthResponse(BaseModel):
    """Sistem sağlık durumu"""
    status: str
    model_loaded: bool
    model_name: str
    model_accuracy: Optional[float]

# ✅ API ENDPOINT'LERI
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Zekai Masnu Crop Recommendation API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Sistem ve model durumunu kontrol et"""
    return HealthResponse(
        status="healthy" if model else "degraded",
        model_loaded=model is not None,
        model_name=metadata.get("best_model", "unknown"),
        model_accuracy=metadata.get("best_f1", None)
    )

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_crop(features: SoilFeatures):
    """
    Toprak ve iklim verilerine göre en uygun mahsulü önerir
    
    **Örnek kullanım:**
    - N: 90, P: 42, K: 43
    - temperature: 21, humidity: 82, ph: 6.5, rainfall: 203
    """
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model yüklenemedi, servis kullanılamıyor")
        
        # Feature'ları doğru sıraya göre diz
        feature_values = [
            features.n,
            features.p,
            features.k,
            features.temperature,
            features.humidity,
            features.ph,
            features.rainfall
        ]
        
        logger.info(f"🔮 Tahmin için gelen veriler: {feature_values}")
        
        # Tahmin yap
        prediction_encoded = model.predict([feature_values])[0]
        
        # Encoded label'ı crop ismine çevir
        crop_name = metadata["label_classes"][prediction_encoded]
        
        # Olasılıkları hesapla (eğer model destekliyorsa)
        probabilities = {}
        if hasattr(model, "predict_proba"):
            probas = model.predict_proba([feature_values])[0]
            for i, prob in enumerate(probas):
                crop = metadata["label_classes"][i]
                probabilities[crop] = float(prob)
        
        # Confidence seviyesi
        confidence = "high"
        if probabilities and max(probabilities.values()) < 0.6:
            confidence = "medium"
        elif probabilities and max(probabilities.values()) < 0.4:
            confidence = "low"
        
        logger.info(f"🌱 Tahmin sonucu: {crop_name} (confidence: {confidence})")
        
        return PredictionResponse(
            recommended_crop=crop_name,
            confidence=confidence,
            model_used=metadata.get("best_model", "unknown"),
            features_used=metadata.get("feature_names", []),
            all_probabilities=probabilities if probabilities else None
        )
        
    except Exception as e:
        logger.error(f"❌ Tahmin hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Tahmin sırasında hata: {str(e)}")

@app.get("/crops", tags=["Information"])
async def list_available_crops():
    """Sistemin bildiği tüm mahsul listesini döndürür"""
    try:
        crops = metadata.get("label_classes", [])
        return {
            "available_crops": crops,
            "total_crops": len(crops)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mahsul listesi alınamadı: {str(e)}")

@app.get("/model-info", tags=["Information"])
async def model_information():
    """Kullanılan model hakkında detaylı bilgi"""
    try:
        return {
            "best_model": metadata.get("best_model", "unknown"),
            "best_f1_score": metadata.get("best_f1", None),
            "feature_names": metadata.get("feature_names", []),
            "training_date": "2025-01-26",  # Dosya adından çıkarılabilir
            "total_classes": len(metadata.get("label_classes", [])),
            "cv_top_models": metadata.get("cv_top", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model bilgisi alınamadı: {str(e)}")

# ✅ BATCH PREDICTION (Opsiyonel)
class BatchPredictionRequest(BaseModel):
    features_list: List[SoilFeatures]

@app.post("/predict-batch", tags=["Prediction"])
async def predict_batch(batch_request: BatchPredictionRequest):
    """Toplu tahmin için - birden fazla veri noktası"""
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model yüklenemedi")
        
        predictions = []
        for features in batch_request.features_list:
            feature_values = [
                features.N, features.P, features.K,
                features.temperature, features.humidity, 
                features.ph, features.rainfall
            ]
            
            prediction_encoded = model.predict([feature_values])[0]
            crop_name = metadata["label_classes"][prediction_encoded]
            
            predictions.append({
                "features": features.dict(),
                "recommended_crop": crop_name
            })
        
        return {
            "predictions": predictions,
            "total_predictions": len(predictions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Toplu tahmin hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "machine_learning_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )