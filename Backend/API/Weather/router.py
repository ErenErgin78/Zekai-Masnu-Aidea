# Weather router - hava durumu API endpoint'leri

import requests
from fastapi import APIRouter


router = APIRouter(prefix="/weather", tags=["Weather"])



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
            return {
                "precipitation_sum": rainfall_data[0],
                "time": day_data[0],
                "temperature_2m_mean": temperature_data[0],
                "wind_direction_10m_dominant": wind_direction_data[0],
                "wind_speed_10m_max": wind_speed_data[0],
                "wind_gusts_10m_max": wind_gusts_data[0],
                "weather_code": weather_code_data[0]
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


# Günlük hava durumu endpoint'i
@router.get("/dailyweather/{latitude}/{longitude}")
async def daily_weather(latitude: float, longitude: float):
    data = get_daily_Data(latitude, longitude)
    if data:
        return data
    return {"error": "Hava durumu verisi alınamadı"}

# Günlük et0(su kaybı hesaplamak için) endpoint'i
@router.get("/dailyet0/{latitude}/{longitude}")
async def daily_et0(latitude: float, longitude: float):
    data = get_daily_et0(latitude, longitude)
    if data:
        return data
    return {"error": "ET0 verisi alınamadı"}