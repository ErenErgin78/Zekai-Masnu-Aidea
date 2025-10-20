# Weather router - hava durumu API endpoint'leri

import requests
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
import re
from typing import Optional
import geocoder
import logging

router = APIRouter(prefix="/weather", tags=["Weather"])


# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic modelleri
class ManualRequest(BaseModel):
    """Manuel koordinat girişi için model"""
    method: str = Field(..., description="Method type", example="Manual")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam (-180 ile 180 arası)")
    latitude: float = Field(..., ge=-90, le=90, description="Enlem (-90 ile 90 arası)")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'manual':
            raise ValueError('Method must be "Manual" for manual coordinates')
        return v.title()
    
    @field_validator('longitude', 'latitude')
    @classmethod
    def validate_coordinates(cls, v):
        """Koordinat değerlerini doğrula ve güvenlik kontrolü yap"""
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        
        # SQL injection koruması - sadece sayısal değerlere izin ver
        if re.search(r'[^0-9.\-]', str(v)):
            raise ValueError('Invalid coordinate format - only numbers, dots and minus allowed')
        
        return float(v)

class AutoRequest(BaseModel):
    """Otomatik konum tespiti için model"""
    method: str = Field(..., description="Method type", example="Auto")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'auto':
            raise ValueError('Method must be "Auto" for automatic location detection')
        return v.title()
    
#API'de kullanılan WMO kodlarının Türkçe açıklamaları
WMO_CODES_TR = {
    0: "Açık",
    1: "Az Bulutlu",
    2: "Parçalı Bulutlu",
    3: "Çok Bulutlu (Kapalı)",
    45: "Sisli",
    48: "Kırağı Sisi",
    51: "Çiseleme (Hafif)",
    53: "Çiseleme (Orta)",
    55: "Çiseleme (Yoğun)",
    56: "Donan Çiseleme (Hafif)",
    57: "Donan Çiseleme (Yoğun)",
    61: "Yağmur (Hafif)",
    63: "Yağmur (Orta)",
    65: "Yağmur (Şiddetli)",
    66: "Donan Yağmur (Hafif)",
    67: "Donan Yağmur (Şiddetli)",
    71: "Kar Yağışı (Hafif)",
    73: "Kar Yağışı (Orta)",
    75: "Kar Yağışı (Şiddetli)",
    77: "Kar Taneleri",
    80: "Sağanak Yağmur (Hafif)",
    81: "Sağanak Yağmur (Orta)",
    82: "Sağanak Yağmur (Şiddetli)",
    85: "Sağanak Kar (Hafif)",
    86: "Sağanak Kar (Şiddetli)",
    95: "Gök Gürültülü Fırtına",
    96: "Gök Gürültülü Fırtına (Hafif Dolu)",
    99: "Gök Gürültülü Fırtına (Şiddetli Dolu)"
}
    

def get_automatic_coordinates() -> tuple[Optional[float], Optional[float]]:
    """
    IP adresinden otomatik konum tespiti
    
    Returns:
        (longitude, latitude) tuple veya (None, None)
        
    Raises:
        Exception: Konum tespit hatası
    """
    try:
        logger.info("Attempting automatic location detection...")
        g = geocoder.ip('me')
        
        if g.ok:
            lat, lon = g.latlng
            logger.info(f"Location detected: Lat={lat}, Lon={lon}")
            return lon, lat
        else:
            logger.warning("Automatic location detection failed")
            return None, None
            
    except Exception as e:
        logger.error(f"Error in automatic location detection: {str(e)}")
        raise Exception(f"Location detection error: {str(e)}")
        

# Günlük hava durumu verilerini al
def get_daily_Data(latitude, longitude):

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return None

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "et0_fao_evapotranspiration,precipitation_sum,temperature_2m_mean,wind_direction_10m_dominant,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
        "timezone": "auto",
        "forecast_days": 1
    }

    try: 
        response = requests.get(url, params=params)
        if response.status_code==200:
            data = response.json()

            rainfall_data = data.get("daily").get("precipitation_sum", [])
            day_data = data.get("daily").get("time", [])
            temperature_data = data.get("daily").get("temperature_2m_mean", [])
            wind_direction_data = data.get("daily").get("wind_direction_10m_dominant", [])
            wind_speed_data = data.get("daily").get("wind_speed_10m_max", [])
            wind_gusts_data = data.get("daily").get("wind_gusts_10m_max", [])
            weather_code_data = data.get("daily").get("weather_code", [])
            weather_code_data = WMO_CODES_TR.get(weather_code_data[0], "Bilinmeyen")
            return {
                "precipitation_sum": rainfall_data[0],
                "time": day_data[0],
                "temperature_2m_mean": temperature_data[0],
                "wind_direction_10m_dominant": wind_direction_data[0],
                "wind_speed_10m_max": wind_speed_data[0],
                "wind_gusts_10m_max": wind_gusts_data[0],
                "weather_code": weather_code_data
            }

            
    except requests.exceptions.RequestException as e:
        return None

#Günlük et0 verilerini al
def get_daily_et0(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "et0_fao_evapotranspiration",
        "timezone": "auto",
        "forecast_days": 1
    }

    try: 
        response = requests.get(url, params=params)
        if response.status_code==200:
            data = response.json()

            et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            day_data = data.get("daily").get("time", [])
            return {
                "et0_fao_evapotranspiration": et0_data[0],
                "time": day_data[0]
            }

            
    except requests.exceptions.RequestException as e:
        return None



@router.post("/dailyweather/auto")
async def daily_weather_auto(request: AutoRequest):
    """Otomatik konum tespiti ile günlük hava durumu"""
    try:
        lon, lat = get_automatic_coordinates()
        if lon is None or lat is None:
            return {"error": "Konum tespit edilemedi"}
            
        data = get_daily_Data(lat, lon)
        if data:
            data["coordinates"] = {"longitude": lon, "latitude": lat}
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}

@router.post("/dailyet0/auto")
async def daily_et0_auto(request: AutoRequest):
    """Otomatik konum tespiti ile günlük ET0 verisi"""
    try:
        lon, lat = get_automatic_coordinates()
        if lon is None or lat is None:
            return {"error": "Konum tespit edilemedi"}
            
        data = get_daily_et0(lat, lon)
        if data:
            data["coordinates"] = {"longitude": lon, "latitude": lat}
            return data
        return {"error": "ET0 verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}

@router.post("/dailyweather/manual")
async def daily_weather_manual(request: ManualRequest):
    """Manuel koordinatlar ile günlük hava durumu"""
    try:
        data = get_daily_Data(request.latitude, request.longitude)
        if data:
            data["coordinates"] = {
                "longitude": request.longitude, 
                "latitude": request.latitude
            }
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}

@router.post("/dailyet0/manual")
async def daily_et0_manual(request: ManualRequest):
    """Manuel koordinatlar ile günlük ET0 verisi"""
    try:
        data = get_daily_et0(request.latitude, request.longitude)
        if data:
            data["coordinates"] = {
                "longitude": request.longitude,
                "latitude": request.latitude
            }
            return data
        return {"error": "ET0 verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}


