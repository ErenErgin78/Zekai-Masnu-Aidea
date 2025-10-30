# tools/data_visualizer_tool.py
import json
from typing import Dict, Any

class DataVisualizerTool:
    def __init__(self):
        self.name = "Data Visualizer Tool"
        self.description = "Verileri görselleştirme ve özetleme"
    
    def create_soil_summary(self, soil_data: Dict) -> Dict[str, Any]:
        """Toprak verilerini özetle"""
        try:
            summary = {
                "soil_id": soil_data.get("soil_id"),
                "classification": soil_data.get("classification", {}),
                "key_properties": {},
                "stats": {}
            }
            
            # Temel özellikler
            for prop in soil_data.get("basic_properties", []):
                summary["key_properties"][prop["name"]] = {
                    "value": prop["value"],
                    "unit": prop.get("unit", "")
                }
            
            # Doku özellikleri
            texture_total = 0
            for prop in soil_data.get("texture_properties", []):
                summary["key_properties"][prop["name"]] = {
                    "value": prop["value"],
                    "unit": prop.get("unit", "")
                }
                if prop["name"] in ["Clay", "Sand", "Silt"]:
                    texture_total += prop["value"]
            
            summary["stats"]["texture_total"] = texture_total
            summary["stats"]["property_count"] = len(summary["key_properties"])
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_text_report(self, soil_data: Dict) -> str:
        """Metin tabanlı rapor oluştur"""
        summary_result = self.create_soil_summary(soil_data)
        
        if not summary_result["success"]:
            return f"Rapor oluşturma hatası: {summary_result['error']}"
        
        summary = summary_result["summary"]
        classification = summary["classification"]
        
        report = f"""
📋 TOPRAK ANALİZ RAPORU
{'='*40}

🆔 Toprak ID: {summary['soil_id']}

🏷️ Sınıflandırma:
   • WRB4: {classification.get('wrb4_code', 'N/A')} - {classification.get('wrb4_description', 'N/A')}
   • WRB2: {classification.get('wrb2_code', 'N/A')} - {classification.get('wrb2_description', 'N/A')}

📊 Özellikler:
"""
        for prop_name, prop_data in summary["key_properties"].items():
            report += f"   • {prop_name}: {prop_data['value']} {prop_data['unit']}\n"
        
        report += f"\n📈 İstatistikler:"
        report += f"\n   • Toplam özellik sayısı: {summary['stats']['property_count']}"
        report += f"\n   • Doku toplamı: {summary['stats']['texture_total']}%"
        
        return report
    
    def __call__(self, soil_data: Dict) -> str:
        """Tool çağrıldığında çalışacak metod"""
        return self.generate_text_report(soil_data)