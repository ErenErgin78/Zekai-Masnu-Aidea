# Weather router - hava durumu API endpoint'leri

import requests
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field, field_validator
import re
from typing import Optional
import geocoder
import logging
from datetime import date,datetime,timedelta

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
    day: int = Field(1, ge=1, le=16, description="Gün sayısı (1-16 arası)", example=1)
    
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

def _validate_dates(start_date: date, end_date: date):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    
    if end_date > date.today() + timedelta(days=16):  # örnek: gelecekte çok ileri tarihleri engelle
        raise HTTPException(status_code=400, detail="end_date too far in the future")
    

async def get_automatic_coordinates() -> tuple[Optional[float], Optional[float]]:
    """
    IP adresinden otomatik konum tespiti
    
    Returns:
        (longitude, latitude) tuple veya (None, None)
        
    Raises:
        Exception: Konum tespit hatası
    """
    try:
        logger.info("Attempting automatic location detection...")
        # <<< YENİ: 'geocoder' bloke edici bir kütüphanedir.
        # FastAPI'nin ana thread'ini kilitlememesi için bir thread'de çalıştırıyoruz.
        g = await asyncio.to_thread(geocoder.ip, 'me')
        
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

# Saatlik hava durumu verilerini al
@cache(namespace="weather-hourly", expire=3600)
async def get_hourly_Data(latitude, longitude,day=1):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation,temperature_2m,relative_humidity_2m,apparent_temperature,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm,soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,soil_temperature_54cm,cape,precipitation_probability,rain,snowfall,snow_depth,wind_direction_10m,wind_speed_10m,wind_gusts_10m,weather_code,showers",
        "timezone": "auto",
        "forecast_days": day
    }

    try: 
        logger.info(f"DIŞ API'ye saatlik istek atılıyor: Lat={latitude}, Lon={longitude}")
        async with httpx.AsyncClient() as client:

            response = await client.get(url, params=params)
            response.raise_for_status()
        if response.status_code==200:
            data = response.json()

            temperature_data = data.get("hourly").get("temperature_2m", [])
            soil_temperature_0cm_data = data.get("hourly").get("soil_temperature_0cm", [])
            soil_temperature_6cm_data = data.get("hourly").get("soil_temperature_6cm", [])
            soil_temperature_18cm_data = data.get("hourly").get("soil_temperature_18cm", [])
            soil_temperature_54cm_data = data.get("hourly").get("soil_temperature_54cm", [])
            soil_moisture_0_to_1cm_data = data.get("hourly").get("soil_moisture_0_to_1cm", [])
            soil_moisture_1_to_3cm_data = data.get("hourly").get("soil_moisture_1_to_3cm", [])
            soil_moisture_3_to_9cm_data = data.get("hourly").get("soil_moisture_3_to_9cm", [])
            soil_moisture_9_to_27cm_data = data.get("hourly").get("soil_moisture_9_to_27cm", [])
            soil_moisture_27_to_81cm_data = data.get("hourly").get("soil_moisture_27_to_81cm", [])
            apparent_temperature_data = data.get("hourly").get("apparent_temperature", [])
            rainfall_data = data.get("hourly").get("precipitation", [])
            rain_data= data.get("hourly").get("rain", [])
            precipitation_probability_data = data.get("hourly").get("precipitation_probability", [])
            relative_humidity_2m_data = data.get("hourly").get("relative_humidity_2m", [])
            snowfall_data = data.get("hourly").get("snowfall", [])
            snow_depth_data = data.get("hourly").get("snow_depth", [])
            showers_data = data.get("hourly").get("showers", [])
            cape_data = data.get("hourly").get("cape", [])
            wind_direction_data = data.get("hourly").get("wind_direction_10m", [])
            wind_speed_data = data.get("hourly").get("wind_speed_10m", [])
            wind_gusts_data = data.get("hourly").get("wind_gusts_10m", [])
            weather_code_data = data.get("hourly").get("weather_code", [])
            weather_code_data = [WMO_CODES_TR.get(code, "Bilinmeyen") for code in weather_code_data]
            time_data = data.get("hourly").get("time", [])

            
            data_by_time = []
            for i, t in enumerate(time_data):
                # güvenli indeksleme ile her zaman tek bir zaman nesnesi oluştur
                entry = {
                    "time": t,
                    "precipitation": rainfall_data[i] if i < len(rainfall_data) else None,
                    "temperature_2m": temperature_data[i] if i < len(temperature_data) else None,
                    "wind_direction_10m": wind_direction_data[i] if i < len(wind_direction_data) else None,
                    "wind_speed_10m": wind_speed_data[i] if i < len(wind_speed_data) else None,
                    "wind_gusts_10m": wind_gusts_data[i] if i < len(wind_gusts_data) else None,
                    "relative_humidity_2m": relative_humidity_2m_data[i] if i < len(relative_humidity_2m_data) else None,
                    "apparent_temperature": apparent_temperature_data[i] if i < len(apparent_temperature_data) else None,
                    "soil_moisture_0_to_1cm": soil_moisture_0_to_1cm_data[i] if i < len(soil_moisture_0_to_1cm_data) else None,
                    "soil_moisture_1_to_3cm": soil_moisture_1_to_3cm_data[i] if i < len(soil_moisture_1_to_3cm_data) else None,
                    "soil_moisture_3_to_9cm": soil_moisture_3_to_9cm_data[i] if i < len(soil_moisture_3_to_9cm_data) else None,
                    "soil_moisture_9_to_27cm": soil_moisture_9_to_27cm_data[i] if i < len(soil_moisture_9_to_27cm_data) else None,
                    "soil_moisture_27_to_81cm": soil_moisture_27_to_81cm_data[i] if i < len(soil_moisture_27_to_81cm_data) else None,
                    "soil_temperature_0cm": soil_temperature_0cm_data[i] if i < len(soil_temperature_0cm_data) else None,
                    "soil_temperature_6cm": soil_temperature_6cm_data[i] if i < len(soil_temperature_6cm_data) else None,
                    "soil_temperature_18cm": soil_temperature_18cm_data[i] if i < len(soil_temperature_18cm_data) else None,
                    "soil_temperature_54cm": soil_temperature_54cm_data[i] if i < len(soil_temperature_54cm_data) else None,
                    "precipitation_probability": precipitation_probability_data[i] if i < len(precipitation_probability_data) else None,
                    "rain": rain_data[i] if i < len(rain_data) else None,
                    "snowfall": snowfall_data[i] if i < len(snowfall_data) else None,
                    "showers": showers_data[i] if i < len(showers_data) else None,
                    "snow_depth": snow_depth_data[i] if i < len(snow_depth_data) else None,
                    "cape": cape_data[i] if i < len(cape_data) else None,
                    "weather_code": weather_code_data[i] if i < len(weather_code_data) else None
                }
                data_by_time.append(entry)
                data_by_time.append({"coordinates": {"longitude": longitude, "latitude": latitude}})

            return data_by_time
            

            
    except httpx.RequestError as e:
        logger.error(f"Hava durumu API isteği hatası (hourly): {e}")
        return None
    except Exception as e:
        logger.error(f"Veri işleme hatası (hourly): {e}")
        return None
    

# Günlük hava durumu verilerini al
@cache(namespace="weather-daily", expire=3600)
async def get_daily_Data(latitude, longitude,days=1):

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "et0_fao_evapotranspiration,precipitation_sum,temperature_2m_mean,apparent_temperature_max,apparent_temperature_mean,apparent_temperature_min,rain_sum,showers_sum,snowfall_sum,precipitation_hours,precipitation_probability_mean,daylight_duration,sunshine_duration,wind_direction_10m_dominant,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
        "timezone": "auto",
        "forecast_days": days
    }

    try:
        logger.info(f"DIŞ API'ye günlük istek atılıyor: Lat={latitude}, Lon={longitude}") 
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        if response.status_code==200:
            data = response.json()

            rainfall_data = data.get("daily").get("precipitation_sum", []),
            daily_et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            apparant_temperature_max_data = data.get("daily").get("apparent_temperature_max", [])
            apparant_temperature_mean_data = data.get("daily").get("apparent_temperature_mean", [])
            apparant_temperature_min_data = data.get("daily").get("apparent_temperature_min", [])
            rain_Sum_data = data.get("daily").get("rain_sum", [])
            showers_Sum_data = data.get("daily").get("showers_sum", [])
            snow_Fall_sum_data = data.get("daily").get("snowfall_sum", [])
            preci_Probability_mean_data = data.get("daily").get("precipitation_probability_mean", [])
            preci_Hours_data = data.get("daily").get("precipitation_hours", [])
            daylight_Duration_data = data.get("daily").get("daylight_duration", [])
            sunshine_Duration_data = data.get("daily").get("sunshine_duration", [])
            day_data = data.get("daily").get("time", [])
            temperature_data = data.get("daily").get("temperature_2m_mean", [])
            daily_et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            wind_direction_data = data.get("daily").get("wind_direction_10m_dominant", [])
            wind_speed_data = data.get("daily").get("wind_speed_10m_max", [])
            wind_gusts_data = data.get("daily").get("wind_gusts_10m_max", [])
            weather_code_data = data.get("daily").get("weather_code", [])
            weather_code_data = WMO_CODES_TR.get(weather_code_data[0], "Bilinmeyen")
            
            data_by_day = []
            for i, d in enumerate(day_data):
                entry={
                    "day":d,
                    "precipitation_sum": rainfall_data[0][i] if i < len(rainfall_data[0]) else None,
                    "et0_fao_evapotranspiration": daily_et0_data[i] if  i < len(daily_et0_data) else None,
                    "temperature_2m_mean": temperature_data[i] if i < len(temperature_data) else None,
                    "apparent_temperature_max": apparant_temperature_max_data[i] if i < len(apparant_temperature_max_data) else None,
                    "apparent_temperature_mean": apparant_temperature_mean_data[i] if i < len(apparant_temperature_mean_data) else None,
                    "apparent_temperature_min": apparant_temperature_min_data[i] if i < len(apparant_temperature_min_data) else None,
                    "rain_sum": rain_Sum_data[i] if i < len(rain_Sum_data) else None,
                    "showers_sum": showers_Sum_data[i] if i < len(showers_Sum_data) else None,
                    "snowfall_sum": snow_Fall_sum_data[i] if i < len(snow_Fall_sum_data) else None,
                    "precipitation_probability_mean": preci_Probability_mean_data[i] if i < len(preci_Probability_mean_data) else None,
                    "precipitation_hours": preci_Hours_data[i] if i < len(preci_Hours_data) else None,
                    "daylight_duration": daylight_Duration_data[i] if i < len(daylight_Duration_data) else None,
                    "sunshine_duration": sunshine_Duration_data[i] if i < len(sunshine_Duration_data) else None,
                    "wind_direction_10m_dominant": wind_direction_data[i] if i < len(wind_direction_data) else None,
                    "wind_speed_10m_max": wind_speed_data[i] if i < len(wind_speed_data) else None,
                    "wind_gusts_10m_max": wind_gusts_data[i] if i < len(wind_gusts_data) else None,
                    "weather_code": weather_code_data
                }
                data_by_day.append(entry)
                data_by_day.append({"coordinates": {"longitude": longitude, "latitude": latitude}})
            return data_by_day
            
    except httpx.RequestError as e:
        logger.error(f"Hava durumu API isteği hatası (daily): {e}")
        return None
    except Exception as e:
        logger.error(f"Veri işleme hatası (daily): {e}")
        return None

@cache(namespace="weather-hourly", expire=3600)
async def get_data_by_date(latitude, longitude, start_date, end_date):
    """ Belirli bir tarih için veri alma fonksiyonu """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": start_date,
    "end_date": end_date,
    "daily": "et0_fao_evapotranspiration,precipitation_sum,temperature_2m_mean,apparent_temperature_max,apparent_temperature_mean,apparent_temperature_min,rain_sum,showers_sum,snowfall_sum,precipitation_hours,precipitation_probability_mean,daylight_duration,sunshine_duration,wind_direction_10m_dominant,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
    "timezone": "auto"
    }

    try: 
        logger.info(f"DIŞ API'ye tarih bazlı istek atılıyor: Lat={latitude}, Lon={longitude}, Start={start_date}, End={end_date}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        
        if response.status_code==200:
            data = response.json()

            rainfall_data = data.get("daily").get("precipitation_sum", []),
            daily_et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            apparant_temperature_max_data = data.get("daily").get("apparent_temperature_max", [])
            apparant_temperature_mean_data = data.get("daily").get("apparent_temperature_mean", [])
            apparant_temperature_min_data = data.get("daily").get("apparent_temperature_min", [])
            rain_Sum_data = data.get("daily").get("rain_sum", [])
            showers_Sum_data = data.get("daily").get("showers_sum", [])
            snow_Fall_sum_data = data.get("daily").get("snowfall_sum", [])
            preci_Probability_mean_data = data.get("daily").get("precipitation_probability_mean", [])
            preci_Hours_data = data.get("daily").get("precipitation_hours", [])
            daylight_Duration_data = data.get("daily").get("daylight_duration", [])
            sunshine_Duration_data = data.get("daily").get("sunshine_duration", [])
            day_data = data.get("daily").get("time", [])
            temperature_data = data.get("daily").get("temperature_2m_mean", [])
            daily_et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            wind_direction_data = data.get("daily").get("wind_direction_10m_dominant", [])
            wind_speed_data = data.get("daily").get("wind_speed_10m_max", [])
            wind_gusts_data = data.get("daily").get("wind_gusts_10m_max", [])
            weather_code_data = data.get("daily").get("weather_code", [])
            weather_code_data = WMO_CODES_TR.get(weather_code_data[0], "Bilinmeyen")
            
            data_by_day = []
            for i, d in enumerate(day_data):
                entry={
                    "day":d,
                    "precipitation_sum": rainfall_data[0][i] if i < len(rainfall_data[0]) else None,
                    "et0_fao_evapotranspiration": daily_et0_data[i] if  i < len(daily_et0_data) else None,
                    "temperature_2m_mean": temperature_data[i] if i < len(temperature_data) else None,
                    "apparent_temperature_max": apparant_temperature_max_data[i] if i < len(apparant_temperature_max_data) else None,
                    "apparent_temperature_mean": apparant_temperature_mean_data[i] if i < len(apparant_temperature_mean_data) else None,
                    "apparent_temperature_min": apparant_temperature_min_data[i] if i < len(apparant_temperature_min_data) else None,
                    "rain_sum": rain_Sum_data[i] if i < len(rain_Sum_data) else None,
                    "showers_sum": showers_Sum_data[i] if i < len(showers_Sum_data) else None,
                    "snowfall_sum": snow_Fall_sum_data[i] if i < len(snow_Fall_sum_data) else None,
                    "precipitation_probability_mean": preci_Probability_mean_data[i] if i < len(preci_Probability_mean_data) else None,
                    "precipitation_hours": preci_Hours_data[i] if i < len(preci_Hours_data) else None,
                    "daylight_duration": daylight_Duration_data[i] if i < len(daylight_Duration_data) else None,
                    "sunshine_duration": sunshine_Duration_data[i] if i < len(sunshine_Duration_data) else None,
                    "wind_direction_10m_dominant": wind_direction_data[i] if i < len(wind_direction_data) else None,
                    "wind_speed_10m_max": wind_speed_data[i] if i < len(wind_speed_data) else None,
                    "wind_gusts_10m_max": wind_gusts_data[i] if i < len(wind_gusts_data) else None,
                    "weather_code": weather_code_data
                }
                data_by_day.append(entry)
                data_by_day.append({"coordinates": {"longitude": longitude, "latitude": latitude}})
            return data_by_day
            
    except httpx.RequestError as e:
        logger.error(f"Hava durumu API isteği hatası (archive): {e}")
        return None
    except Exception as e:
        logger.error(f"Veri işleme hatası (archive): {e}")
        return None


@router.post("/dailyweather/auto")
async def daily_weather_auto(request: AutoRequest, days: int = Query(default=1, ge=1, le=16, description="Gün sayısı (1-16 arası)")):
    """Otomatik konum tespiti ile günlük hava durumu (days optional query param)"""
    try:
        lon, lat = await get_automatic_coordinates()
        if lon is None or lat is None:
            return {"error": "Konum tespit edilemedi"}
            
        data = await get_daily_Data(lat, lon, days) 
        if data:           
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}



@router.post("/dailyweather/manual")
async def daily_weather_manual(request: ManualRequest, days: int = Query(default=1, ge=1, le=16, description="Gün sayısı (1-16 arası)")):
    """Manuel koordinatlar ile günlük hava durumu (days optional query param)"""
    try:
        data = await get_daily_Data(request.latitude, request.longitude, days)
        if data:
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}
    
@router.post("/dailyweather/bydate/manual/{start_date}/{end_date}")
async def daily_weather_by_date(request: ManualRequest, start_date: date, end_date: date):
    """ Belirtilen tarih aralığında manuel koordinatlar ile günlük hava durumu 
        Tarih formatı: YYYY-AA-GG
    """

    try:
        _validate_dates(start_date,end_date)
        data = await get_data_by_date(request.latitude, request.longitude, start_date, end_date)
        if data:
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}

@router.post("/dailyweather/bydate/auto/{start_date}/{end_date}")
async def daily_weather_by_date_auto(request: AutoRequest, start_date: date, end_date: date):
    """ Belirtilen tarih aralığında otomatik konum tespiti ile günlük hava durumu
        Tarih formatı: YYYY-AA-GG
    """
    try:
        _validate_dates(start_date,end_date)
        lon, lat = await get_automatic_coordinates()
        if lon is None or lat is None:
            return {"error": "Konum tespit edilemedi"}
            
        data = await get_data_by_date(lat, lon, start_date, end_date)
        if data:           
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}
        
@router.post("/hourlyweather/auto")
async def hourly_weather_auto(request: AutoRequest, days: int = Query(default=1, ge=1, le=16, description="Gün sayısı (1-16 arası)")):
    """Otomatik konum tespiti ile saatlik hava durumu (days optional query param)"""
    try:
        lon, lat = await get_automatic_coordinates()
        if lon is None or lat is None:
            return {"error": "Konum tespit edilemedi"}
            
        data = await get_hourly_Data(lat, lon, day=days)
        if data:
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}

@router.post("/hourlyweather/manual")
async def hourly_weather_manual(request: ManualRequest, days: int = Query(default=1, ge=1, le=16, description="Gün sayısı (1-16 arası)")):
    """Manuel koordinatlar ile saatlik hava durumu (days optional query param)"""
    
    try:
        data = await get_hourly_Data(request.latitude, request.longitude, day=days)
        if data:
            return data
        return {"error": "Hava durumu verisi alınamadı"}
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}