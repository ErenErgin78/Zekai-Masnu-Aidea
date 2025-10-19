# Weather router - hava durumu API endpoint'leri

import requests
from fastapi import FastAPI

app = FastAPI()





def get_daily_Data(latitude, longitude):

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
            et0_data = data.get("daily").get("et0_fao_evapotranspiration", [])
            rainfall_data = data.get("daily").get("precipitation_sum", [])
            day_data = data.get("daily").get("time", [])
            temperature_data = data.get("daily").get("temperature_2m_mean", [])
            wind_direction_data = data.get("daily").get("wind_direction_10m_dominant", [])
            wind_speed_data = data.get("daily").get("wind_speed_10m_max", [])
            wind_gusts_data = data.get("daily").get("wind_gusts_10m_max", [])
            weather_code_data = data.get("daily").get("weather_code", [])
            return {
                "et0_fao_evapotranspiration": et0_data[0],
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






@app.get("/dailydata/{latitude}/{longitude}")
async def et0_endpoint(latitude: float, longitude: float):
    data = get_daily_Data(latitude, longitude)
    if data:
        return data
    return {"error": "ET0 verisi alınamadı"}

