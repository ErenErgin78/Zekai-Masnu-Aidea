# tools/soil_analyzer_tool.py
from typing import Dict, Any

class SoilAnalyzerTool:
    def __init__(self):
        self.name = "Soil Analyzer Tool"
        self.description = "Toprak özelliklerini analiz eder ve tarımsal öneriler sunar"
    
    def analyze_soil_properties(self, soil_data: Dict) -> Dict[str, Any]:
        """Toprak özelliklerini analiz et"""
        try:
            if "error" in soil_data:
                return {
                    "success": False,
                    "error": soil_data["error"]
                }
            
            analysis = {
                "soil_id": soil_data.get("soil_id", "Bilinmeyen"),
                "soil_quality": "Bilinmeyen",
                "ph_status": "Bilinmeyen",
                "organic_carbon_status": "Bilinmeyen",
                "texture_analysis": {},
                "suitable_crops": [],
                "recommendations": []
            }
            
            # pH analizi
            ph_value = None
            for prop in soil_data.get("basic_properties", []):
                if prop["name"] == "pH":
                    ph_value = prop["value"]
                    if ph_value < 5.5:
                        analysis["ph_status"] = "Asidik"
                        analysis["recommendations"].append("Toprak pH'ını yükseltmek için kireç uygulayın")
                    elif ph_value > 7.5:
                        analysis["ph_status"] = "Bazik"
                        analysis["recommendations"].append("pH'ı düşürmek için organik madde ekleyin")
                    else:
                        analysis["ph_status"] = "Nötr (İdeal)"
                        
                elif prop["name"] == "Organic Carbon":
                    oc_value = prop["value"]
                    if oc_value < 1.0:
                        analysis["organic_carbon_status"] = "Düşük"
                        analysis["recommendations"].append("Organik karbon seviyesini artırın (kompost kullanın)")
                    elif oc_value < 2.0:
                        analysis["organic_carbon_status"] = "Orta"
                    else:
                        analysis["organic_carbon_status"] = "Yüksek (İyi)"
            
            # Doku analizi
            clay = silt = sand = 0
            for prop in soil_data.get("texture_properties", []):
                if prop["name"] == "Clay":
                    clay = prop["value"]
                elif prop["name"] == "Silt":
                    silt = prop["value"]
                elif prop["name"] == "Sand":
                    sand = prop["value"]
            
            analysis["texture_analysis"] = {
                "clay_percent": clay,
                "silt_percent": silt,
                "sand_percent": sand,
                "texture_class": self._determine_texture_class(clay, silt, sand)
            }
            
            # Uygun ürünler
            texture_class = analysis["texture_analysis"]["texture_class"]
            analysis["suitable_crops"] = self._recommend_crops(
                texture_class, 
                ph_value if ph_value else 7.0,
                analysis["organic_carbon_status"]
            )
            
            # Genel kalite değerlendirmesi
            quality_score = 0
            if analysis["ph_status"] == "Nötr (İdeal)":
                quality_score += 35
            elif analysis["ph_status"] in ["Hafif Asidik", "Hafif Bazik"]:
                quality_score += 20
                
            if analysis["organic_carbon_status"] == "Yüksek (İyi)":
                quality_score += 35
            elif analysis["organic_carbon_status"] == "Orta":
                quality_score += 20
                
            if "Tın" in texture_class or "Loam" in texture_class:
                quality_score += 30
            elif texture_class in ["Killi", "Kumlu"]:
                quality_score += 15
            
            if quality_score >= 70:
                analysis["soil_quality"] = "Mükemmel"
            elif quality_score >= 50:
                analysis["soil_quality"] = "İyi"
            elif quality_score >= 30:
                analysis["soil_quality"] = "Orta"
            else:
                analysis["soil_quality"] = "Zayıf"
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _determine_texture_class(self, clay: float, silt: float, sand: float) -> str:
        """Toprak doku sınıfını belirle"""
        if clay > 40:
            return "Killi (Clay)"
        elif clay > 27 and sand > 20 and sand < 45:
            return "Killi Tın (Clay Loam)"
        elif sand > 70:
            return "Kumlu (Sandy)"
        elif sand > 50 and clay < 20:
            return "Kumlu Tın (Sandy Loam)"
        elif silt > 50 and clay < 27:
            return "Siltli Tın (Silty Loam)"
        elif silt > 80:
            return "Siltli (Silty)"
        else:
            return "Tın (Loam)"
    
    def _recommend_crops(self, texture_class: str, ph: float, organic_status: str) -> list:
        """Toprak özelliklerine göre ürün öner"""
        crops = []
        
        # Dokuya göre
        if "Tın" in texture_class or "Loam" in texture_class:
            crops.extend(["Buğday", "Mısır", "Domates", "Patates", "Soğan"])
        elif "Kil" in texture_class or "Clay" in texture_class:
            crops.extend(["Pirinç", "Pamuk", "Ayçiçeği"])
        elif "Kum" in texture_class or "Sandy" in texture_class:
            crops.extend(["Havuç", "Patates", "Üzüm", "Kavun"])
        
        # pH'a göre filtreleme
        if ph < 6.0:
            # Asidik toprak seven bitkiler
            if "Patates" not in crops:
                crops.append("Patates")
            crops = [c for c in crops if c not in ["Soğan", "Pamuk"]]
        elif ph > 7.5:
            # Bazik toprak toleranslı
            crops = [c for c in crops if c not in ["Patates"]]
        
        return crops[:5]  # En fazla 5 öneri
    
    def __call__(self, soil_data: Dict) -> str:
        """Tool çağrıldığında çalışacak metod"""
        result = self.analyze_soil_properties(soil_data)
        
        if not result["success"]:
            return f"❌ Analiz hatası: {result['error']}"
        
        analysis = result["analysis"]
        
        response = f"""🌱 TOPRAK ANALİZ RAPORU

📊 Toprak Kalitesi: {analysis['soil_quality']}

🧪 Temel Özellikler:
   • pH Durumu: {analysis['ph_status']}
   • Organik Karbon: {analysis['organic_carbon_status']}

🏜️ Doku Analizi:
   • Sınıf: {analysis['texture_analysis']['texture_class']}
   • Kil: {analysis['texture_analysis']['clay_percent']}%
   • Silt: {analysis['texture_analysis']['silt_percent']}%
   • Kum: {analysis['texture_analysis']['sand_percent']}%

🌾 Önerilen Ürünler:
   {', '.join(analysis['suitable_crops'])}

💡 Öneriler:
"""
        for rec in analysis['recommendations']:
            response += f"   • {rec}\n"
        
        return response