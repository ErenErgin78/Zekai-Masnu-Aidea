# agents/research_agent.py
from typing import Dict, Any, List

class ResearchAgent:
    def __init__(self, tools: List = None, verbose: bool = True):
        self.name = "Soil Research Agent"
        self.description = "Toprak araştırmaları için akıllı agent"
        self.tools = tools or []
        self.verbose = verbose
        self.conversation_history = []
    
    def research_soil(self, query: str, soil_data: Dict = None) -> Dict[str, Any]:
        """Toprak araştırması yap"""
        try:
            if self.verbose:
                print(f"🔍 Agent araştırıyor: {query}")
            
            research_result = {
                "success": True,
                "query": query,
                "tools_used": [],
                "findings": [],
                "recommendations": []
            }
            
            # Mevcut tool'ları kullan
            for tool in self.tools:
                if self.verbose:
                    print(f"🛠️ Tool kullanılıyor: {tool.name}")
                
                research_result["tools_used"].append(tool.name)
                
                if tool.name == "Soil Analyzer Tool" and soil_data:
                    analysis = tool.analyze_soil_properties(soil_data)
                    if analysis["success"]:
                        research_result["findings"].append({
                            "tool": tool.name,
                            "data": analysis
                        })
                
                elif tool.name == "Data Visualizer Tool" and soil_data:
                    summary = tool.create_soil_summary(soil_data)
                    if summary["success"]:
                        research_result["findings"].append({
                            "tool": tool.name,
                            "data": summary
                        })
            
            # Öneriler oluştur
            research_result["recommendations"] = self._generate_recommendations(research_result)
            
            # Konuşma geçmişine ekle
            self.conversation_history.append({
                "query": query,
                "result": research_result
            })
            
            return research_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Araştırma hatası: {str(e)}"
            }
    
    def _generate_recommendations(self, research_result: Dict) -> List[str]:
        """Araştırma sonuçlarına göre öneriler oluştur"""
        recommendations = []
        
        for finding in research_result["findings"]:
            if finding["tool"] == "Soil Analyzer Tool":
                analysis = finding["data"]
                if analysis["success"]:
                    recs = analysis["analysis"].get("recommendations", [])
                    recommendations.extend(recs)
        
        # Benzersiz öneriler
        unique_recommendations = list(set(recommendations))
        
        # Genel öneriler ekle
        if len(research_result["tools_used"]) > 0:
            unique_recommendations.append("Düzenli toprak analizi yaptırmayı unutmayın")
            unique_recommendations.append("Toprak sağlığı için organik gübre kullanın")
        
        return unique_recommendations
    
    def get_conversation_summary(self) -> str:
        """Konuşma geçmişini özetle"""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        
        summary = f"🤖 {self.name} - Konuşma Özeti\n"
        summary += "=" * 40 + "\n"
        summary += f"Toplam sorgu: {len(self.conversation_history)}\n\n"
        
        for i, conv in enumerate(self.conversation_history, 1):
            summary += f"{i}. Sorgu: {conv['query']}\n"
            summary += f"   Kullanılan tool'lar: {', '.join(conv['result'].get('tools_used', []))}\n"
            summary += f"   Bulgular: {len(conv['result'].get('findings', []))}\n"
            summary += f"   Öneriler: {len(conv['result'].get('recommendations', []))}\n\n"
        
        return summary
    
    def __call__(self, query: str, soil_data: Dict = None) -> str:
        """Agent çağrıldığında çalışacak metod"""
        result = self.research_soil(query, soil_data)
        
        if result["success"]:
            response = f"🔍 ARAŞTIRMA SONUÇLARI: {query}\n\n"
            response += f"🛠️ Kullanılan Tool'lar: {', '.join(result['tools_used'])}\n\n"
            
            # Bulgular
            if result["findings"]:
                response += "📊 BULGULAR:\n"
                for finding in result["findings"]:
                    tool_name = finding["tool"]
                    response += f"   • {tool_name}: {len(finding['data'])} veri noktası\n"
            
            # Öneriler
            if result["recommendations"]:
                response += "\n💡 ÖNERİLER:\n"
                for rec in result["recommendations"]:
                    response += f"   • {rec}\n"
            
            return response
        else:
            return f"❌ Araştırma hatası: {result['error']}"