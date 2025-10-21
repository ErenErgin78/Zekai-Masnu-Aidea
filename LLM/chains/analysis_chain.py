# chains/analysis_chain.py
from typing import Dict, Any, List

class AnalysisChain:
    def __init__(self, tools: List = None):
        self.name = "Soil Analysis Chain"
        self.description = "Toprak analizi için iş akışı zinciri"
        self.tools = tools or []
    
    def run_analysis(self, soil_data: Dict, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analiz zincirini çalıştır"""
        try:
            results = {
                "success": True,
                "analysis_type": analysis_type,
                "steps": [],
                "results": {}
            }
            
            # 1. Adım: Veri özetleme
            if any(tool.name == "Data Visualizer Tool" for tool in self.tools):
                visualizer = next(tool for tool in self.tools if tool.name == "Data Visualizer Tool")
                summary = visualizer.create_soil_summary(soil_data)
                results["steps"].append("data_visualization")
                results["results"]["summary"] = summary
            
            # 2. Adım: Toprak analizi
            if any(tool.name == "Soil Analyzer Tool" for tool in self.tools):
                analyzer = next(tool for tool in self.tools if tool.name == "Soil Analyzer Tool")
                analysis = analyzer.analyze_soil_properties(soil_data)
                results["steps"].append("soil_analysis")
                results["results"]["analysis"] = analysis
            
            # 3. Adım: Rapor oluşturma
            report = self._generate_final_report(results)
            results["results"]["final_report"] = report
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Zincir çalıştırma hatası: {str(e)}"
            }
    
    def _generate_final_report(self, chain_results: Dict) -> str:
        """Nihai rapor oluştur"""
        if not chain_results["success"]:
            return f"Hata: {chain_results['error']}"
        
        report = f"""
🔬 KAPSAMLI TOPRAK ANALİZ RAPORU
{'='*50}

📋 Analiz Türü: {chain_results['analysis_type']}
🔄 İşlenen Adımlar: {', '.join(chain_results['steps'])}

"""
        
        # Özet bilgileri ekle
        if "summary" in chain_results["results"]:
            summary = chain_results["results"]["summary"]
            if summary["success"]:
                report += f"🏷️ Toprak ID: {summary['summary']['soil_id']}\n\n"
        
        # Analiz sonuçlarını ekle
        if "analysis" in chain_results["results"]:
            analysis = chain_results["results"]["analysis"]
            if analysis["success"]:
                report += f"🌱 Kalite Değerlendirmesi: {analysis['analysis']['soil_quality']}\n"
                report += f"🌾 Önerilen Ürünler: {', '.join(analysis['analysis']['suitable_crops'])}\n"
        
        report += f"\n💡 Bu rapor {len(chain_results['steps'])} farklı analiz adımından oluşmaktadır."
        
        return report
    
    def __call__(self, soil_data: Dict) -> str:
        """Chain çağrıldığında çalışacak metod"""
        result = self.run_analysis(soil_data)
        if result["success"]:
            return result["results"]["final_report"]
        else:
            return f"❌ Zincir hatası: {result['error']}"