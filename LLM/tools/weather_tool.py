# tools/weather_tool.py
import requests
import httpx
import asyncio
from typing import Dict, Any, Optional, Tuple
import geocoder

class WeatherTool:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.name = "Weather Tool"
        self.description = "Gerçek hava durumu verilerini sağlar - günlük ve saatlik tahminler"
        self.api_base_url = api_base_url
    
    async def get_automatic_coordinates(self) -> Tuple[Optional[float], Optional[float]]:
        """IP adresinden otomatik konum tespiti"""
        try:
            g = geocoder.ip('me')
            if g.ok:
                lat, lon = g.latlng
                return lon, lat
            return None, None
        except Exception:
            return None, None
    
    async def get_daily_weather_auto(self, days: int = 1) -> Dict[str, Any]:
        """Otomatik konum ile günlük hava durumu"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {"method": "Auto"}
                response = await client.post(
                    f"{self.api_base_url}/weather/dailyweather/auto?days={days}",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_daily_weather_manual(self, longitude: float, latitude: float, days: int = 1) -> Dict[str, Any]:
        """Manuel koordinat ile günlük hava durumu"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {
                    "method": "Manual",
                    "longitude": longitude,
                    "latitude": latitude
                }
                response = await client.post(
                    f"{self.api_base_url}/weather/dailyweather/manual?days={days}",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_hourly_weather_auto(self, days: int = 1) -> Dict[str, Any]:
        """Otomatik konum ile saatlik hava durumu"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {"method": "Auto"}
                response = await client.post(
                    f"{self.api_base_url}/weather/hourlyweather/auto?days={days}",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_hourly_weather_manual(self, longitude: float, latitude: float, days: int = 1) -> Dict[str, Any]:
        """Manuel koordinat ile saatlik hava durumu"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {
                    "method": "Manual",
                    "longitude": longitude,
                    "latitude": latitude
                }
                response = await client.post(
                    f"{self.api_base_url}/weather/hourlyweather/manual?days={days}",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def format_weather_response(self, weather_data: Dict[str, Any], weather_type: str = "daily") -> str:
        """Hava durumu verilerini kullanıcı dostu formatta döndür"""
        if not weather_data.get("success"):
            return f"❌ Hava durumu verisi alınamadı: {weather_data.get('error', 'Bilinmeyen hata')}"
        
        data = weather_data["data"]
        if not isinstance(data, list) or not data:
            return "❌ Hava durumu verisi bulunamadı"
        
        if weather_type == "daily":
            return self._format_daily_weather(data)
        else:
            return self._format_hourly_weather(data)
    
    def _format_daily_weather(self, data: list) -> str:
        """Günlük hava durumu formatla"""
        response = "🌤️ GÜNLÜK HAVA DURUMU\n"
        response += "=" * 40 + "\n\n"
        
        for i, day_data in enumerate(data[:3]):  # İlk 3 gün
            if isinstance(day_data, dict) and "day" in day_data:
                day = day_data.get("day", "Bilinmeyen")
                temp = day_data.get("temperature_2m_mean", "N/A")
                precipitation = day_data.get("precipitation_sum", 0)
                weather_code = day_data.get("weather_code", "Bilinmeyen")
                humidity = day_data.get("relative_humidity_2m", "N/A")
                
                response += f"📅 {day}\n"
                response += f"   🌡️ Sıcaklık: {temp}°C\n"
                response += f"   🌧️ Yağış: {precipitation}mm\n"
                response += f"   🌤️ Durum: {weather_code}\n"
                if humidity != "N/A":
                    response += f"   💧 Nem: {humidity}%\n"
                response += "\n"
        
        return response
    
    def _format_hourly_weather(self, data: list) -> str:
        """Saatlik hava durumu formatla"""
        response = "⏰ SAATLİK HAVA DURUMU\n"
        response += "=" * 40 + "\n\n"
        
        for i, hour_data in enumerate(data[:6]):  # İlk 6 saat
            if isinstance(hour_data, dict) and "time" in hour_data:
                time = hour_data.get("time", "Bilinmeyen")
                temp = hour_data.get("temperature_2m", "N/A")
                humidity = hour_data.get("relative_humidity_2m", "N/A")
                weather_code = hour_data.get("weather_code", "Bilinmeyen")
                
                response += f"🕐 {time}\n"
                response += f"   🌡️ Sıcaklık: {temp}°C\n"
                response += f"   💧 Nem: {humidity}%\n"
                response += f"   🌤️ Durum: {weather_code}\n\n"
        
        return response
    
    async def get_weather_analysis(self, location: Optional[str] = None, coordinates: Optional[Tuple[float, float]] = None, days: int = 1, weather_type: str = "daily") -> str:
        """Ana hava durumu analiz fonksiyonu"""
        try:
            if coordinates:
                # Manuel koordinat kullan
                lon, lat = coordinates
                if weather_type == "daily":
                    result = await self.get_daily_weather_manual(lon, lat, days)
                else:
                    result = await self.get_hourly_weather_manual(lon, lat, days)
            else:
                # Otomatik konum tespiti
                if weather_type == "daily":
                    result = await self.get_daily_weather_auto(days)
                else:
                    result = await self.get_hourly_weather_auto(days)
            
            return self.format_weather_response(result, weather_type)
            
        except Exception as e:
            return f"❌ Hava durumu analizi hatası: {str(e)}"
    
    def __call__(self, input_text: str) -> str:
        """Tool çağrıldığında çalışacak metod (sync wrapper)"""
        return asyncio.run(self.get_weather_analysis())