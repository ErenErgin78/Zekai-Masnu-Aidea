# main.py - Agent ve Chain Entegrasyonlu
import os
import sys
import asyncio
import importlib.util
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

# --- Yol Konfigürasyonu ---
class PathConfig:
    BASE_DIR = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea"
    BACKEND_API = os.path.join(BASE_DIR, "Backend", "API", "SoilType")
    BACKEND_RAG = os.path.join(BASE_DIR, "Backend", "RAG")
    LLM_DIR = os.path.join(BASE_DIR, "LLM")
    AGENTS_DIR = os.path.join(LLM_DIR, "agents")
    CHAINS_DIR = os.path.join(LLM_DIR, "chains")
    TOOLS_DIR = os.path.join(LLM_DIR, "tools")

# Yolları Python path'ine ekle
sys.path.extend([
    PathConfig.BACKEND_API,
    PathConfig.BACKEND_RAG, 
    PathConfig.LLM_DIR,
    PathConfig.AGENTS_DIR,
    PathConfig.CHAINS_DIR,
    PathConfig.TOOLS_DIR
])

# --- pwd modülü fix (Windows için) ---
try:
    import pwd
except ImportError:
    import types
    pwd = types.ModuleType('pwd')
    pwd.getpwnam = lambda x: types.SimpleNamespace(pw_uid=0)
    sys.modules['pwd'] = pwd

# --- Servis Tipleri ---
class ServiceType(Enum):
    SOIL_API = "soil_api"
    GPS_LLM = "gps_llm"
    RAG_CHAT = "rag_chat"
    CUSTOM_TOOL = "custom_tool"
    CHAIN = "chain"
    AGENT = "agent"

# --- Tool/Chain/Agent Tanımı ---
@dataclass
class ToolConfig:
    name: str
    module_path: str
    class_name: str
    init_params: Dict[str, Any] = None
    service_type: ServiceType = ServiceType.CUSTOM_TOOL

# --- Merkezi Servis Yöneticisi ---
class AideaServiceManager:
    def __init__(self):
        self.services = {}
        self.tools = {}
        self.chains = {}
        self.agents = {}
        self._initialized = False
        
    async def initialize_services(self):
        """Temel servisleri başlat"""
        if self._initialized:
            return
            
        print("🚀 Aidea Servis Yöneticisi Başlatılıyor...")
        
        try:
            # 1. Soil API Servisi
            await self._initialize_soil_api()
            
            # 2. GPS-LLM Handler
            await self._initialize_gps_llm()
            
            # 3. RAG Chatbot (Tool'lardan ÖNCE yüklenmelidir!)
            await self._initialize_rag_chat_simple()
            
            # 4. Tool'ları yükle (RAG chatbot hazır olduktan sonra)
            self._load_advanced_tools()
            
            # 5. Chain'leri yükle (Tool'lar hazır olduktan sonra)
            self._load_chains()
            
            # 6. Agent'ları yükle (Tool'lar ve Chain'ler hazır olduktan sonra)
            self._load_agents()
            
            self._initialized = True
            print("✅ Tüm servisler başarıyla başlatıldı!")
            
        except Exception as e:
            print(f"❌ Servis başlatma hatası: {e}")
            raise
    
    async def _initialize_soil_api(self):
        """Soil API servisini başlat"""
        try:
            soil_api_path = os.path.join(PathConfig.BACKEND_API, "soil_api.py")
            spec = importlib.util.spec_from_file_location("soil_api", soil_api_path)
            soil_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(soil_module)
            
            self.services[ServiceType.SOIL_API] = {
                'module': soil_module,
                'status': 'active'
            }
            print("✅ Soil API servisi yüklendi")
            
        except Exception as e:
            print(f"❌ Soil API yükleme hatası: {e}")
            self.services[ServiceType.SOIL_API] = {'status': 'error', 'error': str(e)}
    
    async def _initialize_gps_llm(self):
        """GPS-LLM handler'ı başlat"""
        try:
            gps_handler_path = os.path.join(PathConfig.LLM_DIR, "gps_llm_handler.py")
            spec = importlib.util.spec_from_file_location("gps_llm_handler", gps_handler_path)
            gps_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gps_module)
            
            self.services[ServiceType.GPS_LLM] = {
                'module': gps_module,
                'get_automatic_coordinates': gps_module.get_automatic_coordinates,
                'get_soil_data': gps_module.get_soil_data,
                'generate_llm_answer': gps_module.generate_llm_answer,
                'status': 'active'
            }
            print("✅ GPS-LLM Handler servisi yüklendi")
            
        except Exception as e:
            print(f"❌ GPS-LLM yükleme hatası: {e}")
            self.services[ServiceType.GPS_LLM] = {'status': 'error', 'error': str(e)}
    
    async def _initialize_rag_chat_simple(self):
        """RAG chatbot'u başlat"""
        try:
            rag_processor_path = os.path.join(PathConfig.BACKEND_RAG, "rag_processor.py")
            gemini_client_path = os.path.join(PathConfig.BACKEND_RAG, "gemini_client.py")
            chat_rag_path = os.path.join(PathConfig.BACKEND_RAG, "chat_rag.py")
    
            spec_rag = importlib.util.spec_from_file_location("rag_processor", rag_processor_path)
            rag_module = importlib.util.module_from_spec(spec_rag)
            spec_rag.loader.exec_module(rag_module)
    
            spec_gemini = importlib.util.spec_from_file_location("gemini_client", gemini_client_path)
            gemini_module = importlib.util.module_from_spec(spec_gemini)
            spec_gemini.loader.exec_module(gemini_module)
    
            spec_chat = importlib.util.spec_from_file_location("chat_rag", chat_rag_path)
            chat_module = importlib.util.module_from_spec(spec_chat)
            spec_chat.loader.exec_module(chat_module)
    
            pdfs_path = os.path.join(PathConfig.BACKEND_RAG, "PDFs")
            vector_store_path = os.path.join(PathConfig.BACKEND_RAG, "vector_store")
        
            rag_processor = rag_module.RAGProcessor(
                pdfs_path=pdfs_path,
                vector_store_path=vector_store_path
            )
    
            if not self._check_vector_store_simple(vector_store_path):
                print("🔥 PDF'ler işleniyor...")
                success = rag_processor.load_and_process_pdfs()
                if not success:
                    raise Exception("PDF işleme başarısız")
            else:
                print("✅ Vektör veritabanı hazır")
    
            gemini_client = gemini_module.GeminiClient()
            chatbot_instance = chat_module.RAGChatbot.__new__(chat_module.RAGChatbot)
            chatbot_instance.rag_processor = rag_processor
            chatbot_instance.gemini_client = gemini_client
            chatbot_instance.conversation_history = []
            chatbot_instance.max_sources = 3  # Token tasarrufu için
            chatbot_instance.max_context_length = 3000  # Context token limiti
    
            self.services[ServiceType.RAG_CHAT] = {
                'module': chat_module,
                'processor': rag_processor,
                'gemini_client': gemini_client,
                'chatbot': chatbot_instance,
                'status': 'active'
            }
            print("✅ RAG Chatbot servisi yüklendi")
    
        except Exception as e:
            print(f"❌ RAG Chatbot hatası: {e}")
            self.services[ServiceType.RAG_CHAT] = {'status': 'error', 'error': str(e)}
    
    def _check_vector_store_simple(self, vector_store_path):
        """Vektör veritabanı kontrolü"""
        return os.path.exists(vector_store_path) and os.listdir(vector_store_path)
    
    def _load_advanced_tools(self):
        """Gelişmiş tool'ları yükle"""
        try:
            print("🔧 Tool'lar yükleniyor...")
            
            # Weather Tool
            weather_tool_path = os.path.join(PathConfig.TOOLS_DIR, "weather_tool.py")
            spec_weather = importlib.util.spec_from_file_location("weather_tool", weather_tool_path)
            weather_module = importlib.util.module_from_spec(spec_weather)
            spec_weather.loader.exec_module(weather_module)
            
            # Data Visualizer Tool
            visualizer_tool_path = os.path.join(PathConfig.TOOLS_DIR, "data_visualitor_tool.py")
            spec_visualizer = importlib.util.spec_from_file_location("data_visualitor_tool", visualizer_tool_path)
            visualizer_module = importlib.util.module_from_spec(spec_visualizer)
            spec_visualizer.loader.exec_module(visualizer_module)
            
            # RAG Tool - Import
            try:
                rag_tool_path = os.path.join(PathConfig.TOOLS_DIR, "rag_tool.py")
                spec_rag_tool = importlib.util.spec_from_file_location("rag_tool", rag_tool_path)
                rag_tool_module = importlib.util.module_from_spec(spec_rag_tool)
                spec_rag_tool.loader.exec_module(rag_tool_module)
                print("✅ RAG Tool modülü yüklendi")
            except Exception as e:
                print(f"⚠️ RAG Tool yüklenemedi: {e}")
                rag_tool_module = None
            
            # Soil Analyzer Tool (basit)
            class SoilAnalyzerTool:
                def __init__(self):
                    self.name = "Soil Analyzer Tool"
                    self.description = "Toprak verilerini analiz eder"
                
                def analyze_soil_properties(self, soil_data: Dict) -> Dict[str, Any]:
                    """Toprak özelliklerini analiz et"""
                    try:
                        if "error" in soil_data:
                            return {"success": False, "error": soil_data['error']}
                        
                        # Basit analiz
                        classification = soil_data.get('classification', {})
                        basic_props = soil_data.get('basic_properties', [])
                        
                        # pH kontrolü
                        ph_value = None
                        for prop in basic_props:
                            if prop['name'] == 'pH':
                                ph_value = prop['value']
                                break
                        
                        # Toprak kalitesi değerlendirmesi
                        soil_quality = "Orta"
                        if ph_value:
                            if 6.0 <= ph_value <= 7.5:
                                soil_quality = "İyi"
                            elif ph_value < 5.5 or ph_value > 8.0:
                                soil_quality = "Zayıf"
                        
                        # Ürün önerileri
                        suitable_crops = ["Buğday", "Arpa", "Mısır"]
                        
                        return {
                            "success": True,
                            "analysis": {
                                "soil_quality": soil_quality,
                                "ph_value": ph_value,
                                "suitable_crops": suitable_crops,
                                "recommendations": [
                                    "Düzenli toprak analizi yaptırın",
                                    "Organik gübre kullanın",
                                    "Toprak sağlığını koruyun"
                                ]
                            }
                        }
                        
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                
                def __call__(self, soil_data: Dict) -> str:
                    result = self.analyze_soil_properties(soil_data)
                    if result["success"]:
                        analysis = result["analysis"]
                        return f"Kalite: {analysis['soil_quality']}, pH: {analysis['ph_value']}, Ürünler: {', '.join(analysis['suitable_crops'])}"
                    return f"Analiz hatası: {result['error']}"
            
            # Tool'ları kaydet
            self.tools["weather_tool"] = {
                'instance': weather_module.WeatherTool(),
                'module': weather_module,
                'class': weather_module.WeatherTool
            }
            
            self.tools["data_visualizer_tool"] = {
                'instance': visualizer_module.DataVisualizerTool(),
                'module': visualizer_module,
                'class': visualizer_module.DataVisualizerTool
            }
            
            self.tools["soil_analyzer_tool"] = {
                'instance': SoilAnalyzerTool(),
                'module': None,
                'class': SoilAnalyzerTool
            }
            
            # RAG Tool'u ekle (eğer yüklendiyse)
            if rag_tool_module:
                # RAG chatbot'u al
                rag_chatbot = None
                if ServiceType.RAG_CHAT in self.services:
                    rag_service = self.services[ServiceType.RAG_CHAT]
                    if rag_service.get('status') == 'active':
                        rag_chatbot = rag_service.get('chatbot')
                        print("✅ RAG Chatbot RAG Tool'a bağlandı")
                
                if rag_chatbot:
                    self.tools["rag_tool"] = {
                        'instance': rag_tool_module.RAGTool(
                            rag_chatbot=rag_chatbot,
                            max_response_length=None  # Sınırsız - tam cevap göster
                        ),
                        'module': rag_tool_module,
                        'class': rag_tool_module.RAGTool
                    }
                    print("✅ RAG Tool eklendi (Tam cevap modu)")
                else:
                    print("⚠️ RAG Chatbot bulunamadı, RAG Tool eklenemedi")
            
            print(f"✅ {len(self.tools)} tool yüklendi")
            
        except Exception as e:
            print(f"❌ Tool yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_chains(self):
        """Chain'leri yükle"""
        try:
            # Analysis Chain
            chain_path = os.path.join(PathConfig.CHAINS_DIR, "analysis_chain.py")
            spec_chain = importlib.util.spec_from_file_location("analysis_chain", chain_path)
            chain_module = importlib.util.module_from_spec(spec_chain)
            spec_chain.loader.exec_module(chain_module)
            
            # Tool listesini hazırla
            tool_instances = [tool['instance'] for tool in self.tools.values()]
            
            # Chain instance oluştur
            analysis_chain = chain_module.AnalysisChain(tools=tool_instances)
            
            self.chains["analysis_chain"] = {
                'instance': analysis_chain,
                'module': chain_module,
                'class': chain_module.AnalysisChain
            }
            
            print(f"✅ {len(self.chains)} chain yüklendi")
            
        except Exception as e:
            print(f"❌ Chain yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_agents(self):
        """Agent'ları yükle"""
        try:
            # Research Agent
            agent_path = os.path.join(PathConfig.AGENTS_DIR, "research_agents.py")
            spec_agent = importlib.util.spec_from_file_location("research_agents", agent_path)
            agent_module = importlib.util.module_from_spec(spec_agent)
            spec_agent.loader.exec_module(agent_module)
            
            # Tool listesini hazırla
            tool_instances = [tool['instance'] for tool in self.tools.values()]
            
            # Agent instance oluştur
            research_agent = agent_module.ResearchAgent(tools=tool_instances, verbose=True)
            
            self.agents["research_agent"] = {
                'instance': research_agent,
                'module': agent_module,
                'class': agent_module.ResearchAgent
            }
            
            print(f"✅ {len(self.agents)} agent yüklendi")
            
        except Exception as e:
            print(f"❌ Agent yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    # --- Servis Erişim Metodları ---
    
    async def soil_analysis(self, longitude: float, latitude: float):
        """Toprak analizi yap"""
        gps_service = self.services[ServiceType.GPS_LLM]
        return await gps_service['get_soil_data'](longitude, latitude)
    
    async def automatic_location_analysis(self):
        """Otomatik konum analizi"""
        gps_service = self.services[ServiceType.GPS_LLM]
        lon, lat = await gps_service['get_automatic_coordinates']()
        
        if lon is None or lat is None:
            raise ValueError("Otomatik konum tespiti başarısız")
        
        soil_data = await gps_service['get_soil_data'](lon, lat)
        explanation = gps_service['generate_llm_answer'](
            (lon, lat), soil_data, "Otomatik konum tespiti"
        )
        
        return {
            'coordinates': {'longitude': lon, 'latitude': lat},
            'soil_data': soil_data,
            'explanation': explanation
        }
    
    def rag_chat(self, question: str):
        """RAG chatbot ile konuş"""
        service = self.services[ServiceType.RAG_CHAT]
        chatbot = service['chatbot']
        response, sources = chatbot.query(question)
        return response, sources
    
    def analyze_with_tool(self, tool_name: str, input_data):
        """Tool ile analiz"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool bulunamadı: {tool_name}")
        return tool(input_data)
    
    def run_chain(self, chain_name: str, input_data: Dict, analysis_type: str = "comprehensive"):
        """Chain çalıştır"""
        chain = self.get_chain(chain_name)
        if not chain:
            raise ValueError(f"Chain bulunamadı: {chain_name}")
        return chain.run_analysis(input_data, analysis_type)
    
    def run_agent(self, agent_name: str, query: str, soil_data: Dict = None):
        """Agent çalıştır"""
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent bulunamadı: {agent_name}")
        return agent.research_soil(query, soil_data)
    
    def get_tool(self, tool_name: str):
        """Tool getir"""
        return self.tools.get(tool_name, {}).get('instance')
    
    def get_chain(self, chain_name: str):
        """Chain getir"""
        return self.chains.get(chain_name, {}).get('instance')
    
    def get_agent(self, agent_name: str):
        """Agent getir"""
        return self.agents.get(agent_name, {}).get('instance')
    
    def list_services(self):
        """Tüm servisleri listele"""
        return {
            'services': [s.value for s in self.services.keys()],
            'tools': list(self.tools.keys()),
            'chains': list(self.chains.keys()),
            'agents': list(self.agents.keys())
        }

# --- Global Service Manager ---
service_manager = AideaServiceManager()

# --- Ana Uygulama ---
async def main():
    """Ana uygulama"""
    print("🌍 Aidea Merkezi Sistem")
    print("=" * 50)
    
    await service_manager.initialize_services()
    
    while True:
        print("\n🔧 Kullanılabilir Servisler:")
        services = service_manager.list_services()
        for service_type, service_list in services.items():
            print(f"  {service_type}: {service_list}")
        
        print("\n🎮 İşlem Seçin:")
        print("1. Manuel Toprak Analizi")
        print("2. Otomatik Konum Analizi")
        print("3. RAG Sohbet")
        print("4. Tool ile Analiz")
        print("5. Chain ile Analiz")
        print("6. Agent ile Araştırma")
        print("7. Servis Bilgileri")
        print("8. Çıkış")
        
        choice = input("\nSeçiminiz (1-8): ").strip()
        
        if choice == '1':
            try:
                lon = float(input("Boylam: "))
                lat = float(input("Enlem: "))
                result = await service_manager.soil_analysis(lon, lat)
                print(f"📊 Toprak Verisi: {result.get('soil_id', 'N/A')}")
            except Exception as e:
                print(f"❌ Hata: {e}")
                
        elif choice == '2':
            try:
                result = await service_manager.automatic_location_analysis()
                print(f"📍 Koordinatlar: {result['coordinates']}")
                print(f"🌱 Açıklama: {result['explanation']}")
            except Exception as e:
                print(f"❌ Hata: {e}")
                
        elif choice == '3':
            try:
                question = input("Soru: ")
                response, sources = service_manager.rag_chat(question)
                print(f"🤖 Cevap: {response}")
                if sources:
                    print(f"📚 Kaynaklar: {len(sources)} adet")
            except Exception as e:
                print(f"❌ Hata: {e}")
            
        elif choice == '4':
            try:
                print("\n🛠️ Mevcut Tool'lar:")
                for tool_name in service_manager.tools.keys():
                    tool_desc = service_manager.tools[tool_name]['instance'].description
                    print(f"  - {tool_name}: {tool_desc}")
                
                tool_choice = input("\nTool seçin: ")
                
                if tool_choice == "weather_tool":
                    city = input("Şehir: ")
                    result = service_manager.analyze_with_tool(tool_choice, city)
                    print(f"🌤️ Sonuç: {result}")
                
                elif tool_choice == "rag_tool":
                    question = input("Soru: ")
                    result = service_manager.analyze_with_tool(tool_choice, question)
                    print(f"📚 Sonuç:\n{result}")
                
                elif tool_choice in ["soil_analyzer_tool", "data_visualizer_tool"]:
                    lon = float(input("Boylam: "))
                    lat = float(input("Enlem: "))
                    soil_data = await service_manager.soil_analysis(lon, lat)
                    result = service_manager.analyze_with_tool(tool_choice, soil_data)
                    print(f"🌱 Sonuç: {result}")
                
            except Exception as e:
                print(f"❌ Hata: {e}")
                
        elif choice == '5':
            try:
                print("\n⛓️ Mevcut Chain'ler:")
                for chain_name in service_manager.chains.keys():
                    print(f"  - {chain_name}")
                
                chain_choice = input("Chain seçin: ")
                
                if chain_choice == "analysis_chain":
                    lon = float(input("Boylam: "))
                    lat = float(input("Enlem: "))
                    soil_data = await service_manager.soil_analysis(lon, lat)
                    
                    result = service_manager.run_chain(chain_choice, soil_data)
                    
                    if result["success"]:
                        print(f"\n{result['results']['final_report']}")
                    else:
                        print(f"❌ Chain hatası: {result['error']}")
                
            except Exception as e:
                print(f"❌ Hata: {e}")
                
        elif choice == '6':
            try:
                print("\n🤖 Mevcut Agent'lar:")
                for agent_name in service_manager.agents.keys():
                    print(f"  - {agent_name}")
                
                agent_choice = input("Agent seçin: ")
                
                if agent_choice == "research_agent":
                    query = input("Araştırma sorusu: ")
                    
                    use_soil = input("Toprak verisi kullan? (e/h): ").lower()
                    soil_data = None
                    
                    if use_soil == 'e':
                        lon = float(input("Boylam: "))
                        lat = float(input("Enlem: "))
                        soil_data = await service_manager.soil_analysis(lon, lat)
                    
                    result = service_manager.run_agent(agent_choice, query, soil_data)
                    
                    if result["success"]:
                        print(f"\n🔍 Bulgular: {len(result['findings'])} adet")
                        print(f"💡 Öneriler:")
                        for rec in result["recommendations"]:
                            print(f"  • {rec}")
                    else:
                        print(f"❌ Agent hatası: {result['error']}")
                
            except Exception as e:
                print(f"❌ Hata: {e}")
                
        elif choice == '7':
            services = service_manager.list_services()
            for service_type, service_list in services.items():
                print(f"{service_type}: {service_list}")
                
        elif choice == '8':
            print("👋 Görüşmek üzere!")
            break
            
        else:
            print("❌ Geçersiz seçim!")

if __name__ == "__main__":
    asyncio.run(main())