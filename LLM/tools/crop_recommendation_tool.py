import os
import sys
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ DINAMIK DOSYA YOLU AYARLARI
# Tool'un bulunduğu dizin
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Tool dizini: {TOOL_DIR}")

# API URL - development için local, production için değişebilir
API_BASE_URL = "http://localhost:8002"

class SoilParameters(BaseModel):
    """Toprak parametreleri modeli"""
    nitrogen: float = Field(..., description="Azot seviyesi (N)", ge=0, le=140)
    phosphorus: float = Field(..., description="Fosfor seviyesi (P)", ge=5, le=145)
    potassium: float = Field(..., description="Potasyum seviyesi (K)", ge=5, le=205)
    temperature: float = Field(..., description="Sıcaklık (°C)", ge=0, le=50)
    humidity: float = Field(..., description="Nem oranı (%)", ge=10, le=100)
    ph: float = Field(..., description="Toprak pH değeri", ge=3.5, le=10)
    rainfall: float = Field(..., description="Yağış miktarı (mm)", ge=20, le=300)

class CropRecommendationResponse(BaseModel):
    """Mahsul öneri cevabı"""
    recommended_crop: str
    confidence: str
    model_used: str
    explanation: str
    alternative_crops: Optional[List[str]] = None
    technical_details: Optional[Dict[str, Any]] = None

class CropRecommendationTool:
    """Zekai Masnu - Akıllı Mahsul Öneri Aracı"""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.name = "crop_recommendation_tool"
        self.description = """
        Toprak ve iklim verilerine dayalı olarak en uygun mahsulü önerir.
        
        GEREKLİ PARAMETRELER:
        - nitrogen (N): 0-140 arası
        - phosphorus (P): 5-145 arası  
        - potassium (K): 5-205 arası
        - temperature: 0-50°C arası
        - humidity: 10-100% arası
        - ph: 3.5-10 arası
        - rainfall: 20-300 mm arası
        
        ÖRNEK KULLANIM:
        "90 birim azot, 42 birim fosfor, 43 birim potasyum, 
         21°C sıcaklık, %82 nem, 6.5 pH, 203 mm yağış için 
         hangi mahsulü önerirsin?"
        """
        
        # API bağlantısını test et
        self._test_connection()
    
    def _test_connection(self):
        """API bağlantısını test et"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ ML API'ye başarıyla bağlanıldı")
                return True
            else:
                logger.warning("⚠️ ML API'ye bağlanılamadı")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ML API bağlantı hatası: {e}")
            return False
    
    def _call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """API'ye istek gönder"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Geçersiz method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception("API zaman aşımına uğradı. Lütfen daha sonra tekrar deneyin.")
        except requests.exceptions.ConnectionError:
            raise Exception("ML API'ye bağlanılamadı. API'nin çalıştığından emin olun.")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 422:
                raise Exception("Geçersiz parametreler. Lütfen parametre aralıklarını kontrol edin.")
            else:
                raise Exception(f"API hatası: {str(e)}")
        except Exception as e:
            raise Exception(f"Beklenmeyen hata: {str(e)}")
    
    def get_available_crops(self) -> List[str]:
        """Sistemin bildiği tüm mahsulleri listele"""
        try:
            data = self._call_api("/crops")
            return data.get("available_crops", [])
        except Exception as e:
            logger.error(f"Mahsul listesi alınamadı: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Model bilgilerini getir"""
        try:
            return self._call_api("/model-info")
        except Exception as e:
            logger.error(f"Model bilgisi alınamadı: {e}")
            return {}
    
    def recommend_crop(self, 
                      nitrogen: float,
                      phosphorus: float, 
                      potassium: float,
                      temperature: float,
                      humidity: float,
                      ph: float,
                      rainfall: float) -> CropRecommendationResponse:
        """
        Toprak ve iklim verilerine göre mahsul önerisi yapar
        
        Args:
            nitrogen: Azot seviyesi (0-140)
            phosphorus: Fosfor seviyesi (5-145)
            potassium: Potasyum seviyesi (5-205)
            temperature: Sıcaklık (°C) (0-50)
            humidity: Nem oranı (%) (10-100)
            ph: Toprak pH değeri (3.5-10)
            rainfall: Yağış miktarı (mm) (20-300)
            
        Returns:
            CropRecommendationResponse: Öneri ve detaylı bilgiler
        """
        
        # Parametre validasyonu
        soil_params = SoilParameters(
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            temperature=temperature,
            humidity=humidity,
            ph=ph,
            rainfall=rainfall
        )
        
        logger.info(f"🌱 Mahsul önerisi isteniyor: N={nitrogen}, P={phosphorus}, K={potassium}")
        
        # API'ye istek gönder
        api_data = {
            "n": nitrogen,
            "p": phosphorus,
            "k": potassium,
            "temperature": temperature,
            "humidity": humidity,
            "ph": ph,
            "rainfall": rainfall
        }
        
        try:
            # Tahmin isteği
            prediction_data = self._call_api("/predict", "POST", api_data)
            
            # Alternatif mahsulleri al
            available_crops = self.get_available_crops()
            recommended_crop = prediction_data["recommended_crop"]
            
            # Önerilen mahsulü listeden çıkar ve alternatifleri al
            alternative_crops = [crop for crop in available_crops if crop != recommended_crop]
            
            # Açıklama oluştur
            explanation = self._generate_explanation(prediction_data, soil_params)
            
            return CropRecommendationResponse(
                recommended_crop=recommended_crop,
                confidence=prediction_data.get("confidence", "unknown"),
                model_used=prediction_data.get("model_used", "unknown"),
                explanation=explanation,
                alternative_crops=alternative_crops[:5],  # İlk 5 alternatif
                technical_details={
                    "features_used": prediction_data.get("features_used", []),
                    "all_probabilities": prediction_data.get("all_probabilities", {})
                }
            )
            
        except Exception as e:
            logger.error(f"Mahsul önerisi hatası: {e}")
            raise Exception(f"Mahsul önerisi alınamadı: {str(e)}")
    
    def _generate_explanation(self, prediction_data: Dict, soil_params: SoilParameters) -> str:
        """Kullanıcı dostu açıklama oluştur"""
        
        recommended_crop = prediction_data["recommended_crop"]
        confidence = prediction_data.get("confidence", "unknown")
        
        # Güven seviyesine göre açıklama
        confidence_text = {
            "high": "yüksek güvenilirlikle",
            "medium": "orta güvenilirlikle", 
            "low": "düşük güvenilirlikle"
        }.get(confidence, "")
        
        # Toprak koşullarına göre özelleştirilmiş açıklama
        conditions = []
        
        if soil_params.ph < 5.5:
            conditions.append("asidik toprak")
        elif soil_params.ph > 7.5:
            conditions.append("bazik toprak")
        else:
            conditions.append("nötr pH'lı toprak")
            
        if soil_params.temperature > 30:
            conditions.append("sıcak iklim")
        elif soil_params.temperature < 15:
            conditions.append("serin iklim")
        else:
            conditions.append("ılıman iklim")
            
        if soil_params.rainfall > 200:
            conditions.append("yüksek yağış")
        elif soil_params.rainfall < 100:
            conditions.append("düşük yağış")
        else:
            conditions.append("orta yağış")
        
        conditions_text = ", ".join(conditions)
        
        explanation = (
            f"🌱 **{recommended_crop}** mahsulünü {confidence_text} öneriyorum. "
            f"Verdiğiniz toprak ve iklim verileri ({conditions_text}) bu mahsul için uygun görünüyor. "
        )
        
        # Olasılık bilgisi ekle
        if prediction_data.get("all_probabilities"):
            probs = prediction_data["all_probabilities"]
            top_3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
            if len(top_3) > 1:
                alt_crops = [f"{crop} (%{prob*100:.1f})" for crop, prob in top_3[1:]]
                explanation += f" Diğer olası mahsuller: {', '.join(alt_crops)}."
        
        return explanation
    
    def batch_recommendation(self, parameters_list: List[Dict]) -> List[Dict]:
        """Toplu mahsul önerisi"""
        results = []
        for params in parameters_list:
            try:
                result = self.recommend_crop(**params)
                results.append({
                    "parameters": params,
                    "recommendation": result.dict()
                })
            except Exception as e:
                results.append({
                    "parameters": params,
                    "error": str(e)
                })
        
        return results

# ✅ TOOL INSTANCE - Research Agent için kullanılacak
crop_recommender_tool = CropRecommendationTool()

# ✅ TEST FONKSIYONU
def test_tool():
    """Tool'u test etmek için"""
    print("🧪 Mahsul Öneri Tool Testi...")
    
    try:
        # Tool instance
        tool = CropRecommendationTool()
        
        # Model bilgisi
        model_info = tool.get_model_info()
        print(f"🤖 Model: {model_info.get('best_model', 'Bilinmiyor')}")
        
        # Mevcut mahsuller
        crops = tool.get_available_crops()
        print(f"🌾 Mevcut mahsuller: {len(crops)} adet")
        
        # Test önerisi
        test_params = {
            "nitrogen": 90,
            "phosphorus": 42, 
            "potassium": 43,
            "temperature": 21,
            "humidity": 82,
            "ph": 6.5,
            "rainfall": 203
        }
        
        print("🔮 Test tahmini yapılıyor...")
        recommendation = tool.recommend_crop(**test_params)
        
        print(f"✅ Önerilen mahsul: {recommendation.recommended_crop}")
        print(f"📊 Güven seviyesi: {recommendation.confidence}")
        print(f"💡 Açıklama: {recommendation.explanation}")
        
        return recommendation
        
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
        return None

if __name__ == "__main__":
    # Tool'u test et
    test_tool()