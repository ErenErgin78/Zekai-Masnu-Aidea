# tools/ml_tool.py
from typing import Any, Dict, List, Optional
import httpx


class MLRecommendationTool:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.name = "ML Recommendation Tool"
        self.description = "Toprak + iklim özelliklerinden makine öğrenmesi ile ürün önerir"
        self.base_url = base_url.rstrip("/")

    async def recommend(self, use_auto_location: bool = True, longitude: Optional[float] = None, latitude: Optional[float] = None) -> Dict[str, Any]:
        """ML API'yi çağırıp öneri döndür."""
        try:
            payload: Dict[str, Any]
            if use_auto_location:
                payload = {"method": "Auto"}
            else:
                if longitude is None or latitude is None:
                    return {"success": False, "error": "Koordinatlar gerekli (longitude, latitude)"}
                payload = {"method": "Manual", "coordinates": {"longitude": float(longitude), "latitude": float(latitude)}}

            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.base_url}/ml/analyze", json=payload, timeout=30.0)
                if resp.status_code != 200:
                    return {"success": False, "error": f"ML API Error: {resp.status_code}", "detail": resp.text}
                data = resp.json()
                return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_recommendations(self, ml_response: Dict[str, Any]) -> str:
        """LLM'ye verilecek kullanıcı dostu çıktı hazırla."""
        if not ml_response.get("success"):
            return f"❌ ML öneri hatası: {ml_response.get('error', 'Bilinmeyen hata')}"

        data = ml_response.get("data", {})
        coords = data.get("coordinates", {})
        recs: List[Dict[str, Any]] = data.get("recommendations", [])
        model_info = data.get("model_info", {})

        lines: List[str] = []
        lines.append("🌾 Makine öğrenmesi modeli, toprak ve iklim verilerine göre şu bitkileri önerdi:")
        if coords:
            lines.append(f"📍 Konum: Boylam={coords.get('longitude')}, Enlem={coords.get('latitude')}")

        if recs:
            for i, r in enumerate(recs, 1):
                lines.append(f"  {i}. {r.get('plant_name')} (güven: {r.get('confidence_score')}%, olasılık: {r.get('probability')})")
        else:
            lines.append("  Öneri bulunamadı")

        if model_info:
            lines.append(f"🧠 Model: {model_info.get('model_type')} | Ölçekleyici: {model_info.get('scaler_type')} | Fallback: {model_info.get('fallback_mode')}")

        return "\n".join(lines)

    async def __call__(self, use_auto_location: bool = True, longitude: Optional[float] = None, latitude: Optional[float] = None) -> str:
        result = await self.recommend(use_auto_location=use_auto_location, longitude=longitude, latitude=latitude)
        return self.format_recommendations(result)


