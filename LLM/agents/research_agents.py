# agents/research_agent.py
from typing import Dict, Any, List
import sys
import os

# Tool'ları import et
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

try:
    from soil_analyzer_tool import SoilAnalyzerTool
    print("✅ Soil Analyzer Tool yüklendi")
except ImportError as e:
    print(f"❌ Soil Analyzer Tool yüklenemedi: {e}")
    # Fallback class
    class SoilAnalyzerTool:
        def __init__(self): 
            self.name = "Soil Analyzer Tool"
        def __call__(self, soil_data): 
            return "Soil analyzer mevcut değil"

try:
    from data_visualitor_tool import DataVisualizerTool
    print("✅ Data Visualizer Tool yüklendi")
except ImportError as e:
    print(f"❌ Data Visualizer Tool yüklenemedi: {e}")
    # Fallback class
    class DataVisualizerTool:
        def __init__(self): 
            self.name = "Data Visualizer Tool"
        def create_soil_summary(self, soil_data): 
            return {"success": False, "error": "Tool bulunamadı"}

try:
    from rag_tool import RAGTool
    print("✅ RAG Tool yüklendi")
except ImportError as e:
    print(f"❌ RAG Tool yüklenemedi: {e}")
    # Fallback class
    class RAGTool:
        def __init__(self): 
            self.name = "RAG Knowledge Tool"
        def __call__(self, query): 
            return "RAG mevcut değil"

try:
    from weather_tool import WeatherTool
    print("✅ Weather Tool yüklendi")
except ImportError as e:
    print(f"❌ Weather Tool yüklenemedi: {e}")
    # Fallback class
    class WeatherTool:
        def __init__(self): 
            self.name = "Weather Tool"
        def __call__(self, city): 
            return "Hava durumu mevcut değil"

class ResearchAgent:
    def __init__(self, tools: list = None, verbose: bool = True):
        self.name = "Soil Research Agent"
        self.description = "Toprak araştırmaları için akıllı agent"
        self.verbose = verbose
        self.conversation_history = []
        
        # ✅ CRITICAL FIX: Tool'ları parametreden al VEYA yeni oluştur
        if tools:
            self.tools = tools
            print(f"✅ Research Agent harici tool'larla başlatıldı: {len(self.tools)} tool")
        else:
            # Eğer tool verilmezse, kendi tool'larını oluştur
            self.tools = [
                WeatherTool(),
                DataVisualizerTool(),
                SoilAnalyzerTool(),
                RAGTool()
            ]
            print(f"✅ Research Agent kendi tool'larıyla başlatıldı: {len(self.tools)} tool")
    
    def research_soil(self, query: str, soil_data: Dict = None) -> Dict[str, Any]:
        """Toprak araştırması yap - GÜNCELLENMİŞ"""
        try:
            if self.verbose:
                print(f"🔍 Agent araştırıyor: {query}")
                if soil_data:
                    print(f"📍 Soil data mevcut: {soil_data.get('soil_id', 'Bilinmeyen ID')}")
                    # Soil data içeriğini kontrol et
                    if 'classification' in soil_data:
                        soil_type = soil_data['classification'].get('wrb4_description', 'Bilinmiyor')
                        print(f"📍 Toprak türü: {soil_type}")
                else:
                    print("⚠️ Soil data yok")
            
            research_result = {
                "success": True,
                "query": query,
                "tools_used": [],
                "findings": [],
                "recommendations": []
            }
            
            # ✅ DEĞİŞİKLİK: Soil data varsa ÖNCE onu işle
            if soil_data:
                # Soil Analyzer Tool ile analiz et
                soil_tool = next((tool for tool in self.tools if tool.name == "Soil Analyzer Tool"), None)
                if soil_tool:
                    try:
                        soil_result = soil_tool(soil_data)
                        research_result["findings"].append({
                            "tool": "Soil Analyzer Tool",
                            "data": soil_result,
                            "type": "soil_analysis"
                        })
                        research_result["tools_used"].append("Soil Analyzer Tool")
                        print(f"✅ Soil data başarıyla analiz edildi")
                    except Exception as e:
                        print(f"❌ Soil analyzer hatası: {e}")
                
                # Data Visualizer ile özet oluştur
                visualizer_tool = next((tool for tool in self.tools if tool.name == "Data Visualizer Tool"), None)
                if visualizer_tool and hasattr(visualizer_tool, 'create_soil_summary'):
                    try:
                        summary_result = visualizer_tool.create_soil_summary(soil_data)
                        research_result["findings"].append({
                            "tool": "Data Visualizer Tool", 
                            "data": summary_result,
                            "type": "soil_summary"
                        })
                        research_result["tools_used"].append("Data Visualizer Tool")
                    except Exception as e:
                        print(f"❌ Data visualizer hatası: {e}")
            
            # ✅ RAG Tool - HER ZAMAN çalışsın (sorguya dayalı bilgi)
            rag_tool = next((tool for tool in self.tools if "RAG" in tool.name), None)
            if rag_tool:
                try:
                    rag_result = rag_tool(query)
                    research_result["findings"].append({
                        "tool": rag_tool.name,
                        "data": rag_result,
                        "type": "rag_knowledge"
                    })
                    research_result["tools_used"].append(rag_tool.name)
                    print(f"✅ RAG bilgisi alındı")
                except Exception as e:
                    print(f"❌ RAG hatası: {e}")
            
            # ✅ Weather Tool - Sorguda şehir varsa çalışsın
            weather_tool = next((tool for tool in self.tools if "Weather" in tool.name), None)
            if weather_tool:
                city = self._extract_city_from_query(query)
                if city:
                    try:
                        weather_result = weather_tool(city)
                        research_result["findings"].append({
                            "tool": weather_tool.name,
                            "data": weather_result,
                            "type": "weather_info"
                        })
                        research_result["tools_used"].append(weather_tool.name)
                        print(f"✅ Hava durumu bilgisi alındı: {city}")
                    except Exception as e:
                        print(f"❌ Weather tool hatası: {e}")
            
            # ✅ Eğer hiç bulgu yoksa, fallback bilgiler ekle
            if not research_result["findings"]:
                research_result["findings"] = self._get_fallback_findings(query, soil_data)
                print("ℹ️ Fallback bilgiler kullanıldı")
            
            # ✅ Öneriler oluştur
            research_result["recommendations"] = self._generate_recommendations(research_result, soil_data)
            
            # Konuşma geçmişine ekle
            self.conversation_history.append({
                "query": query,
                "result": research_result
            })
            
            if self.verbose:
                print(f"✅ Araştırma tamamlandı: {len(research_result['findings'])} bulgu, {len(research_result['recommendations'])} öneri")
            
            return research_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Araştırma hatası: {str(e)}",
                "tools_used": [],
                "findings": [],
                "recommendations": ["Sistem geçici olarak hata verdi, lütfen tekrar deneyin"]
            }
            print(f"💥 Research Agent kritik hata: {e}")
            import traceback
            traceback.print_exc()
            return error_result
    
    def _extract_city_from_query(self, query: str) -> str:
        """Query'den şehir adını çıkar"""
        cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Adana", "Kayseri", "Samsun", "Trabzon"]
        
        for city in cities:
            if city.lower() in query.lower():
                return city
        return None
    
    def _get_fallback_findings(self, query: str, soil_data: Dict = None) -> List[Dict]:
        """Tool'lar çalışmazsa fallback bilgiler sağla"""
        findings = []
        
        # Domates yetiştiriciliği için genel bilgiler
        if "domates" in query.lower():
            findings.append({
                "tool": "General Knowledge",
                "data": {
                    "title": "Organik Domates Yetiştiriciliği",
                    "soil_requirements": "İyi drene edilmiş, organik maddece zengin, pH 6.0-6.8",
                    "climate_requirements": "Sıcak iklim, bol güneş, 20-30°C ideal",
                    "key_points": [
                        "Don olaylarına hassas",
                        "Düzenli sulama gerektirir", 
                        "Organik gübreleme önemli"
                    ]
                },
                "type": "fallback_knowledge"
            })
        
        # Toprak verisi varsa basit analiz
        if soil_data:
            findings.append({
                "tool": "Basic Soil Analysis",
                "data": {
                    "soil_id": soil_data.get('soil_id', 'Bilinmiyor'),
                    "classification": soil_data.get('classification', {}).get('wrb4_description', 'Bilinmiyor'),
                    "ph": self._extract_ph_from_soil_data(soil_data),
                    "organic_carbon": self._extract_organic_carbon(soil_data)
                },
                "type": "basic_soil_data"
            })
        
        return findings
    
    def _extract_ph_from_soil_data(self, soil_data: Dict) -> str:
        """Soil data'dan pH değerini çıkar"""
        try:
            basic_props = soil_data.get('basic_properties', [])
            for prop in basic_props:
                if prop.get('name') == 'pH':
                    return prop.get('value', 'Bilinmiyor')
            return 'Bilinmiyor'
        except:
            return 'Bilinmiyor'
    
    def _extract_organic_carbon(self, soil_data: Dict) -> str:
        """Soil data'dan organik karbon değerini çıkar"""
        try:
            basic_props = soil_data.get('basic_properties', [])
            for prop in basic_props:
                if prop.get('name') == 'Organic Carbon':
                    return prop.get('value', 'Bilinmiyor')
            return 'Bilinmiyor'
        except:
            return 'Bilinmiyor'
    
    def _generate_recommendations(self, research_result: Dict, soil_data: Dict = None) -> List[str]:
        """Araştırma sonuçlarına göre öneriler oluştur"""
        recommendations = []
        
        # Bulgulardan öneriler oluştur
        for finding in research_result["findings"]:
            data = finding["data"]
            
            if finding["type"] == "soil_analysis" and isinstance(data, str):
                # Soil analyzer string sonucundan öneriler çıkar
                if "pH'ı düşürmek" in data or "asitli" in data.lower():
                    recommendations.append("Toprak pH'sını düşürmek için organik madde ekleyin")
                if "kireç uygulayın" in data or "bazik" in data.lower():
                    recommendations.append("Toprak pH'sını yükseltmek için kireç uygulayın")
                if "kompost kullanın" in data or "organik" in data.lower():
                    recommendations.append("Organik karbon seviyesini artırmak için kompost kullanın")
            
            elif finding["type"] == "fallback_knowledge":
                if "domates" in research_result["query"].lower():
                    recommendations.extend([
                        "Toprak pH'sını 6.0-6.8 arasında tutun",
                        "Organik kompost ve yanmış gübre kullanın",
                        "Düzenli sulama yapın ancak aşırı sulamadan kaçının",
                        "Don riski olan dönemlerde koruma önlemi alın"
                    ])
        
        # Benzersiz öneriler
        unique_recommendations = list(set(recommendations))
        
        # Genel öneriler ekle
        if len(research_result["tools_used"]) > 0 or research_result["findings"]:
            unique_recommendations.extend([
                "Düzenli toprak analizi yaptırmayı unutmayın",
                "Toprak sağlığı için organik gübre kullanın",
                "Mahsul rotasyonu uygulayın"
            ])
        
        # Soil data'ya göre spesifik öneriler
        if soil_data:
            ph_value = self._extract_ph_from_soil_data(soil_data)
            if ph_value != 'Bilinmiyor' and isinstance(ph_value, (int, float)):
                if ph_value < 6.0:
                    unique_recommendations.append("Toprak pH'sını yükseltmek için kireç uygulayın")
                elif ph_value > 7.0:
                    unique_recommendations.append("Toprak pH'sını düşürmek için organik materyal ekleyin")
        
        return unique_recommendations[:10]  # İlk 10 öneriyi sınırla
    
    def get_conversation_summary(self) -> str:
        """Konuşma geçmişini özetle"""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        
        summary = f"🤖 {self.name} - Konuşma Özeti\n"
        summary += "=" * 50 + "\n"
        summary += f"Toplam sorgu: {len(self.conversation_history)}\n\n"
        
        for i, conv in enumerate(self.conversation_history, 1):
            summary += f"{i}. Sorgu: {conv['query']}\n"
            summary += f"   Kullanılan tool'lar: {', '.join(conv['result'].get('tools_used', []))}\n"
            summary += f"   Bulgular: {len(conv['result'].get('findings', []))}\n"
            summary += f"   Öneriler: {len(conv['result'].get('recommendations', []))}\n"
            
            # Bulgu detayları
            findings = conv['result'].get('findings', [])
            if findings:
                summary += f"   Bulgu Tipleri: {', '.join(set(f['type'] for f in findings))}\n"
            
            summary += "\n"
        
        return summary
    
    def __call__(self, query: str, soil_data: Dict = None) -> str:
        """Agent çağrıldığında çalışacak metod"""
        result = self.research_soil(query, soil_data)
        
        if result["success"]:
            response = f"🔍 ARAŞTIRMA SONUÇLARI: {query}\n\n"
            response += f"🛠️ Kullanılan Tool'lar: {', '.join(result['tools_used']) if result['tools_used'] else 'Hiçbiri'}\n\n"
            
            # Bulgular
            if result["findings"]:
                response += "📊 BULGULAR:\n"
                for i, finding in enumerate(result["findings"], 1):
                    tool_name = finding["tool"]
                    data = finding["data"]
                    
                    if finding["type"] == "fallback_knowledge":
                        response += f"   {i}. {tool_name}:\n"
                        response += f"      - {data.get('title', '')}\n"
                        response += f"      - Toprak: {data.get('soil_requirements', 'Bilinmiyor')}\n"
                        response += f"      - İklim: {data.get('climate_requirements', 'Bilinmiyor')}\n"
                    
                    elif finding["type"] == "basic_soil_data":
                        response += f"   {i}. {tool_name}:\n"
                        response += f"      - Toprak ID: {data.get('soil_id', 'Bilinmiyor')}\n"
                        response += f"      - Sınıf: {data.get('classification', 'Bilinmiyor')}\n"
                        response += f"      - pH: {data.get('ph', 'Bilinmiyor')}\n"
                        response += f"      - Organik Karbon: {data.get('organic_carbon', 'Bilinmiyor')}\n"
                    
                    elif finding["type"] == "weather_info":
                        response += f"   {i}. {tool_name}:\n"
                        if isinstance(data, str) and len(data) > 100:
                            response += f"      - {data[:100]}...\n"
                        else:
                            response += f"      - {data}\n"
                    
                    elif finding["type"] == "soil_analysis":
                        response += f"   {i}. {tool_name}:\n"
                        if isinstance(data, str):
                            response += f"      - {data}\n"
                        else:
                            response += f"      - {str(data)[:100]}...\n"
                    
                    elif finding["type"] == "soil_summary":
                        response += f"   {i}. {tool_name}:\n"
                        if isinstance(data, dict):
                            if data.get('success'):
                                response += f"      - Toprak Türü: {data.get('soil_type', 'Bilinmiyor')}\n"
                                response += f"      - pH Seviyesi: {data.get('ph_level', 'Bilinmiyor')}\n"
                                response += f"      - Organik Madde: {data.get('organic_matter', 'Bilinmiyor')}\n"
                            else:
                                response += f"      - Hata: {data.get('error', 'Bilinmeyen hata')}\n"
                        else:
                            response += f"      - {str(data)[:100]}...\n"
                    
                    elif finding["type"] == "rag_knowledge":
                        response += f"   {i}. {tool_name}:\n"
                        if isinstance(data, str):
                            # RAG cevabını kısalt
                            lines = data.split('\n')
                            for line in lines[:3]:  # İlk 3 satırı göster
                                if line.strip():
                                    response += f"      - {line.strip()}\n"
                            if len(data) > 200:
                                response += f"      - ...\n"
                        else:
                            response += f"      - {str(data)[:100]}...\n"
                    
                    else:
                        response += f"   {i}. {tool_name}: {type(data).__name__}\n"
            
            # Öneriler
            if result["recommendations"]:
                response += "\n💡 ÖNERİLER:\n"
                for rec in result["recommendations"]:
                    response += f"   • {rec}\n"
            else:
                response += "\n⚠️ Bu sorgu için özel öneri bulunamadı.\n"
            
            return response
        else:
            return f"❌ Araştırma hatası: {result['error']}"