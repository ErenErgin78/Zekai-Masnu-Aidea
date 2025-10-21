# tools/weather_tool.py
import requests
from typing import Dict, Any

class WeatherTool:
    def __init__(self, api_key: str = None):
        self.name = "Weather Tool"
        self.description = "Hava durumu bilgisi sağlar"
        self.api_key = api_key
    
    def get_weather(self, city: str) -> Dict[str, Any]:
        """Şehir için hava durumu bilgisi getir"""
        try:
            # Basit bir mock response - gerçek API entegrasyonu yapılabilir
            weather_data = {
                "İstanbul": {"sıcaklık": "25°C", "durum": "güneşli", "nem": "%65"},
                "Ankara": {"sıcaklık": "22°C", "durum": "parçalı bulutlu", "nem": "%60"},
                "İzmir": {"sıcaklık": "28°C", "durum": "açık", "nem": "%70"},
                "Konya": {"sıcaklık": "20°C", "durum": "rüzgarlı", "nem": "%55"}
            }
            
            if city in weather_data:
                return {
                    "success": True,
                    "city": city,
                    "data": weather_data[city],
                    "source": "mock_api"
                }
            else:
                return {
                    "success": False,
                    "error": f"{city} için veri bulunamadı",
                    "available_cities": list(weather_data.keys())
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def __call__(self, input_text: str) -> str:
        """Tool çağrıldığında çalışacak metod"""
        result = self.get_weather(input_text)
        if result["success"]:
            data = result["data"]
            return f"{input_text} hava durumu: {data['sıcaklık']}, {data['durum']}, nem {data['nem']}"
        else:
            return f"Hata: {result['error']}"