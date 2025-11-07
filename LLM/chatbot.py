# chatbot.py - Gemini Function Calling ile Multi-Tool ChatBot
import os
import json
import time
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class OrganicFarmingChatBot:
    """
    Gemini Function Calling ile çalışan akıllı tarım asistanı.
    Kullanıcı isteğine göre otomatik olarak tool, chain veya agent seçer.
    """
    
    def __init__(self, service_manager, model_name: str = "models/gemini-2.5-flash"):
        """
        Args:
            service_manager: UmayServiceManager instance
            model_name: Gemini model adı
        """
        self.service_manager = service_manager
        self.conversation_history = []
        self.max_history = 10  # Son 10 mesajı tut
        
        # Gemini API setup
        try:
            api_key = os.environ["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
        except KeyError:
            raise ValueError("GEMINI_API_KEY ortam değişkeni bulunamadı!")
        
        # Function declarations
        self.tools = self._create_function_declarations()
        
        # Model oluştur (function calling ile)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools
        )
        
        # Chat session - MANUEL function calling kullanacağız
        self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)
        
        print(f"✅ ChatBot başlatıldı: {model_name}")
        print(f"🔧 {len(self.tools)} tool tanımlandı")
    
    def _create_function_declarations(self):
        """Gemini için function declarations oluştur - GÜNCELLENMİŞ"""
        
        function_declarations = [
            {
                "name": "get_weather",
                "description": "Gerçek hava durumu verilerini getirir. Günlük ve saatlik tahminler, sıcaklık, nem, yağış, rüzgar bilgileri sağlar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "weather_type": {
                            "type": "STRING",
                            "description": "Hava durumu türü: 'daily' (günlük) veya 'hourly' (saatlik)",
                            "enum": ["daily", "hourly"]
                        },
                        "days": {
                            "type": "NUMBER",
                            "description": "Kaç günlük tahmin (1-16 arası, varsayılan 1)"
                        },
                        "longitude": {
                            "type": "NUMBER",
                            "description": "Boylam koordinatı (manuel konum için)"
                        },
                        "latitude": {
                            "type": "NUMBER",
                            "description": "Enlem koordinatı (manuel konum için)"
                        },
                        "use_auto_location": {
                            "type": "BOOLEAN",
                            "description": "Otomatik konum tespiti kullan (true) veya manuel koordinat (false)"
                        }
                    },
                    "required": ["weather_type", "use_auto_location"]
                }
            },
            {
                "name": "analyze_soil",
                "description": "Verilen koordinatlardaki toprak özelliklerini analiz eder. pH, organik karbon, doku analizi ve tarımsal öneriler sunar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "longitude": {
                            "type": "NUMBER",
                            "description": "Boylam koordinatı (-180 ile 180 arası)"
                        },
                        "latitude": {
                            "type": "NUMBER", 
                            "description": "Enlem koordinatı (-90 ile 90 arası)"
                        }
                    },
                    "required": ["longitude", "latitude"]
                }
            },
            {
                "name": "get_automatic_location_soil",
                "description": "Kullanıcının mevcut konumunu otomatik tespit ederek o bölgenin toprak analizini yapar. Konum izni gerektirir.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "query_organic_farming_knowledge",
                "description": "Organik tarım bilgi bankasından (RAG) bilgi getirir. Organik tarım, kompost, gübreleme, haşere kontrolü, sertifikasyon gibi konularda detaylı bilgi verir.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "question": {
                            "type": "STRING",
                            "description": "Organik tarım ile ilgili soru"
                        }
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "comprehensive_soil_analysis",
                "description": "Kapsamlı toprak analizi yapar. Toprak verilerini görselleştirir, detaylı analiz yapar ve tarımsal öneriler sunar. Birden fazla tool'u chain olarak kullanır.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "longitude": {
                            "type": "NUMBER",
                            "description": "Boylam koordinatı"
                        },
                        "latitude": {
                            "type": "NUMBER",
                            "description": "Enlem koordinatı"
                        }
                    },
                    "required": ["longitude", "latitude"]
                }
            },
            {
                "name": "ml_crop_recommendation",
                "description": "Toprak ve iklim verilerine göre ML modeliyle ürün önerisi yapar (Auto veya Manual).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "use_auto_location": {"type": "BOOLEAN", "description": "Otomatik konum tespiti kullan"},
                        "longitude": {"type": "NUMBER", "description": "Boylam (Manual için)"},
                        "latitude": {"type": "NUMBER", "description": "Enlem (Manual için)"}
                    },
                    "required": ["use_auto_location"]
                }
            },
            {
                "name": "research_agent_query",
                "description": "Akıllı araştırma agent'ı kullanarak karmaşık sorulara cevap verir. Birden fazla tool'u kullanarak derinlemesine araştırma yapar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "Araştırma sorusu"
                        },
                        "use_soil_data": {
                            "type": "BOOLEAN",
                            "description": "Toprak verisi kullanılsın mı?"
                        },
                        "longitude": {
                            "type": "NUMBER",
                            "description": "Toprak verisi için boylam (use_soil_data true ise gerekli)"
                        },
                        "latitude": {
                            "type": "NUMBER", 
                            "description": "Toprak verisi için enlem (use_soil_data true ise gerekli)"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        return function_declarations
    
    def _get_system_prompt(self) -> str:
        """Chatbot için system prompt - GÜNCELLENMİŞ"""
        return """Sen Türk çiftçilere yardımcı olan organik tarım uzmanı bir asistansın. Adın "UMAY Tarım Asistanı".

🎯 GÖREVIN:
- Toprak analizi yaparak çiftçilere tarımsal öneriler sunmak
- Gerçek hava durumu verilerini sağlamak (günlük ve saatlik tahminler)
- Organik tarım konularında bilgi vermek
- Kullanıcının ihtiyacına göre en uygun tool'ları kullanmak
- Hava durumu ve toprak analizini birleştirerek kapsamlı tarımsal öneriler sunmak

🔧 KULLANABILECEĞIN TOOL'LAR:

1. **get_weather**: Gerçek hava durumu verileri (günlük/saatlik)
   - Kullanım: Hava durumu sorularında, tarımsal planlama için
   - Otomatik konum tespiti veya manuel koordinat kullanabilir
   - Günlük ve saatlik tahminler sağlar

2. **analyze_soil**: Koordinata göre toprak analizi
   - Kullanım: Belirli bir koordinat için toprak bilgisi istendiğinde

3. **get_automatic_location_soil**: Otomatik konum tespiti ile toprak analizi
   - Kullanım: "Bulunduğum yerdeki toprak nasıl?" gibi sorularda

4. **query_organic_farming_knowledge**: Organik tarım bilgi bankası (RAG)
   - Kullanüm: Organik tarım teknikleri, sertifikasyon, kompost vs. sorularında

5. **comprehensive_soil_analysis**: Kapsamlı toprak raporu (Chain)
   - Kullanım: Detaylı toprak analizi istendiğinde

6. **research_agent_query**: Akıllı araştırma agent'ı
   - Kullanım: Karmaşık, çok yönlü sorularda


📋 TOOL SEÇME STRATEJİSİ:

**Basit Sorular** → Tek tool:
- "Hava durumu nasıl?" → get_weather (otomatik konum)
- "32.5, 37.8 koordinatındaki toprak nasıl?" → analyze_soil
- "Organik gübre nasıl yapılır?" → query_organic_farming_knowledge


**Orta Seviye** → Chain kullan:
- "Bu koordinattaki toprağı detaylı analiz et" → comprehensive_soil_analysis

**Karmaşık Sorular** → Birden fazla tool veya agent kullan:
- "Bulunduğum yerde hangi ürünler yetişir ve nasıl organik yetiştiririm?" → research_agent_query + analyze_soil
- "Bu bölgenin hava durumu ve toprak yapısına göre ne önerirsiniz?" → get_weather + analyze_soil
- "Gübreleme ve sulama için hava durumu nasıl?" → get_weather + analyze_soil (birleşik analiz)

🎨 CEVAPLAMA KURALLARI:
1. **Türkçe ve samimi** bir dille konuş
2. **Emoji** kullan ama abartma (🌱 🌾 ☀️ 💧)
3. **Somut öneriler** ver
4. **Tool sonuçlarını** kullanıcı dostu formatta sun
5. Birden fazla tool kullanmak gerekiyorsa, **otomatik olarak** kullan

⚠️ ÖNEMLİ:
- Koordinat sorularında ONDALIKLI sayı kullan (32.5, 37.8)
- Kullanıcıdan eksik bilgi varsa **sor**
- Tool hatası varsa **kibarca** açıkla ve alternatif sun
- **Karmaşık sorularda birden fazla tool kullanmaktan çekinme**

🔍 TOOL KULLANIM KURALI:
- Bir tool (fonksiyon) kullanmaya karar verdiysen, SADECE o tool'un sonucunu kullan!
- Tool çalıştığında kendi bilgini kullanarak ekstra açıklama yapma!

🎯 RESEARCH AGENT KULLANIMI:
- Kullanıcı karmaşık bir tarım sorusu sorduğunda research_agent_query kullan
- Eğer kullanıcı konum belirtiyorsa veya "bulunduğum yer" diyorsa, use_soil_data=true yap ve koordinatları ekle
- Mümkün olduğunca soil data ile zenginleştirilmiş araştırma yap

📍 KOORDINAT ALMA STRATEJİSİ:
- "Bu bölgede", "şu koordinatlarda", "İstanbul'da" gibi ifadelerde koordinatları ara
- Koordinat verilmediyse kullanıcının kendi konumundaki bilgileri istediğini varsay ve otomatik mevcut konuma göre işlem yap.
- Mevcut konum için: get_automatic_location_soil kullan

🚫 ÇOK ÖNEMLİ KURAL:
- Eğer kullanıcı hava durumu, toprak analizi veya organik tarım ile İLGİLİ OLMAYAN bir soru sorarsa,
- "Üzgünüm, ben sadece hava durumu, toprak analizi ve organik tarım konularında yardımcı olabilirim. Başka konularda size yardım edemem." şeklinde cevap ver.
- ASLA kendi alanın dışındaki konularda cevap vermeye çalışma veya uydurma.
- Eğer bir konuda yeterli bilgin yoksa veya tool'lar cevap veremiyorsa, "Bu konuda şu an size yardımcı olamıyorum" de.

Şimdi kullanıcıya yardımcı olmaya hazırsın! 🌱"""
    
    async def chat_async(self, user_message: str) -> str:
        """
        Kullanıcı mesajını işle ve cevap üret (async) - JSON formatında response döndürür
        
        Args:
            user_message: Kullanıcının mesajı
            
        Returns:
            JSON formatında chatbot cevabı
        """
        try:
            # Konuşma geçmişine ekle
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # System prompt ile başla (ilk mesajsa)
            if len(self.conversation_history) == 1:
                context = self._get_system_prompt() + "\n\n" + user_message
            else:
                context = user_message
            
            print(f"📨 Gemini'ye gönderiliyor: {context[:100]}...")
            
            # Gemini'ye gönder
            response = self.chat_session.send_message(context)
            
            # GELİŞTİRİLMİŞ Function calling - BİRDEN FAZLA TOOL DESTEĞİ
            bot_response = await self._handle_function_calls(response)
            
            # Konuşma geçmişine ekle
            self.conversation_history.append({
                "role": "assistant", 
                "content": bot_response
            })
            
            # Geçmiş limitini kontrol et
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            # JSON formatında response döndür
            json_response = {
                "success": True,
                "response": bot_response,
                "timestamp": time.time(),
                "conversation_id": len(self.conversation_history) // 2
            }
            
            return json.dumps(json_response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"❌ Bir hata oluştu: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Hata durumunda da JSON formatında döndür
            error_response = {
                "success": False,
                "error": error_msg,
                "timestamp": time.time(),
                "conversation_id": len(self.conversation_history) // 2
            }
            
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    async def _handle_function_calls(self, response) -> str:
        """
        Birden fazla function call'ı handle et - GÜNCELLENMİŞ
        """
        function_calls = []
        has_text_response = False
        text_response = ""

        # Response'u parse et
        if (hasattr(response, 'candidates') and 
            response.candidates and 
            hasattr(response.candidates[0].content, 'parts') and 
            response.candidates[0].content.parts):
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append(part.function_call)
                elif hasattr(part, 'text') and part.text:
                    has_text_response = True
                    text_response += part.text

        # ✅ DEĞİŞİKLİK: Eğer function call varsa, text response'u YOK SAY
        if function_calls:
            # SADECE function results ile devam et
            function_results = []
            for function_call in function_calls:
                function_name = function_call.name
                function_args = {}
                
                # Argümanları dict'e çevir
                if hasattr(function_call, 'args'):
                    for key, value in function_call.args.items():
                        function_args[key] = value
                
                print(f"🔧 Tool çağrısı: {function_name}")
                print(f"📋 Parametreler: {json.dumps(function_args, indent=2, ensure_ascii=False)}")
                
                # Function'ı çalıştır
                function_result = await self._execute_function(function_name, function_args)
                print(f"📦 Function sonucu: {function_result[:200]}...")
                
                function_results.append({
                    "name": function_name,
                    "result": function_result
                })

            # Birden fazla function sonucunu Gemini'ye gönder
            if len(function_results) == 1:
                function_response_part = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=function_results[0]["name"],
                        response={"result": function_results[0]["result"]}
                    )
                )
                final_response = self.chat_session.send_message(function_response_part)
            else:
                function_response_parts = []
                for func_result in function_results:
                    function_response_parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=func_result["name"],
                                response={"result": func_result["result"]}
                            )
                        )
                    )
                final_response = self.chat_session.send_message(function_response_parts)

            return final_response.candidates[0].content.parts[0].text
        else:
            # Function call yoksa direkt text cevabını döndür
            return response.text if hasattr(response, 'text') else text_response
    
    def chat(self, user_message: str) -> str:
        """Senkron chat metodu (kolaylık için)"""
        import asyncio
        return asyncio.run(self.chat_async(user_message))
    
    async def _execute_function(self, function_name: str, args: Dict) -> Any:
        """Function call'ları çalıştır - GÜNCELLENMİŞ"""
        
        try:
            if function_name == "get_weather":
                tool = self.service_manager.get_tool("weather_tool")
                if tool:
                    weather_type = args.get("weather_type", "daily")
                    days = args.get("days", 1)
                    use_auto_location = args.get("use_auto_location", True)
                    longitude = args.get("longitude")
                    latitude = args.get("latitude")
                    
                    print(f"🌤️ Hava durumu sorgulanıyor: {weather_type}, {days} gün")
                    
                    if use_auto_location:
                        result = await tool.get_weather_analysis(
                            days=days, 
                            weather_type=weather_type
                        )
                    else:
                        if longitude is None or latitude is None:
                            return "Manuel konum için koordinatlar gerekli. Boylam ve enlem değerlerini girin."
                        result = await tool.get_weather_analysis(
                            coordinates=(longitude, latitude),
                            days=days,
                            weather_type=weather_type
                        )
                    
                    return result
                else:
                    return "Hava durumu tool'u kullanılamıyor"
                
            elif function_name == "analyze_soil":
                lon = args.get("longitude")
                lat = args.get("latitude")
                
                if lon is None or lat is None:
                    return "Koordinatlar eksik. Lütfen boylam ve enlem değerlerini girin."
                
                print(f"🌱 Toprak analizi yapılıyor: {lon}, {lat}")
                soil_data = await self.service_manager.soil_analysis(lon, lat)
                
                tool = self.service_manager.get_tool("soil_analyzer_tool")
                if tool:
                    result = tool(soil_data)
                    return result
                else:
                    return f"Toprak analizi: {soil_data}"
                
            elif function_name == "get_automatic_location_soil":
                try:
                    print("📍 Otomatik konum analizi yapılıyor...")
                    result = await self.service_manager.automatic_location_analysis()
                    return result.get("explanation", "Otomatik konum analizi başarısız")
                except Exception as e:
                    return f"Otomatik konum analizi hatası: {str(e)}"
                
            elif function_name == "query_organic_farming_knowledge":
                tool = self.service_manager.get_tool("rag_tool")
                if tool:
                    question = args.get("question", "")
                    print(f"📚 RAG sorgusu: {question}")
                    result = tool(question)
                    return result
                else:
                    return "RAG tool'u kullanılamıyor"
                
            elif function_name == "comprehensive_soil_analysis":
                lon = args.get("longitude")
                lat = args.get("latitude")
                
                if lon is None or lat is None:
                    return "Koordinatlar eksik. Lütfen boylam ve enlem değerlerini girin."
                
                print(f"🔍 Kapsamlı toprak analizi: {lon}, {lat}")
                soil_data = await self.service_manager.soil_analysis(lon, lat)
                
                chain = self.service_manager.get_chain("analysis_chain")
                if chain:
                    result = chain.run_analysis(soil_data)
                    
                    if result.get("success"):
                        return result["results"].get("final_report", "Analiz tamamlandı")
                    else:
                        return f"Analiz hatası: {result.get('error', 'Bilinmeyen hata')}"
                else:
                    return "Analysis chain kullanılamıyor"
            
            elif function_name == "ml_crop_recommendation":
                # ML Recommendation Tool'u çalıştır
                try:
                    from tools.ml_tool import MLRecommendationTool
                    tool = MLRecommendationTool(base_url="http://localhost:8003")
                    # Her zaman otomatik konum kullan (manuel koordinatları yok say)
                    result_text = await tool(use_auto_location=True, longitude=None, latitude=None)
                    return result_text
                except Exception as e:
                    return f"ML öneri aracı hatası: {e}"
                    
            elif function_name == "research_agent_query":
                query = args.get("query", "")
                use_soil = args.get("use_soil_data", True)
                
                print(f"🔬 Araştırma agent'ı: {query}")
                print(f"📍 Soil data kullanımı: {use_soil}")
                
                soil_data = None
                # ✅ DEĞİŞİKLİK: Koordinat varsa MUTLAKA soil data al
                lon = args.get("longitude")
                lat = args.get("latitude")
                
                if lon is not None and lat is not None:
                    print(f"📍 Koordinatlar mevcut: {lon}, {lat} - Soil data alınıyor...")
                    try:
                        soil_data = await self.service_manager.soil_analysis(lon, lat)
                        print(f"✅ Soil data alındı: {soil_data.get('soil_id', 'Bilinmeyen ID')}")
                        
                        # Soil data içeriğini kontrol et
                        if 'classification' in soil_data:
                            soil_type = soil_data['classification'].get('wrb4_description', 'Bilinmiyor')
                            print(f"📍 Toprak türü: {soil_type}")
                        
                    except Exception as e:
                        print(f"❌ Soil data alınamadı: {e}")
                        soil_data = None
                else:
                    print("ℹ️ Koordinat yok - soil data kullanılmayacak")
                
                # ✅ CRITICAL FIX: Service Manager'dan agent al VEYA yeni oluştur
                try:
                    # Önce service manager'dan dene
                    agent = self.service_manager.get_agent("research_agent")
                    if agent:
                        print(f"✅ Service Manager'dan Research Agent alındı")
                    else:
                        # Service manager'da yoksa, yeni oluştur
                        from research_agents import ResearchAgent
                        
                        # Service manager'dan tool'ları al
                        tool_instances = []
                        for tool_name in ['weather_tool', 'data_visualizer_tool', 'soil_analyzer_tool', 'rag_tool']:
                            tool = self.service_manager.get_tool(tool_name)
                            if tool:
                                tool_instances.append(tool)
                                print(f"✅ Tool eklendi: {tool_name}")
                        
                        agent = ResearchAgent(tools=tool_instances, verbose=True)
                        print(f"✅ Yeni Research Agent oluşturuldu: {len(tool_instances)} tool ile")
                    
                    # Agent'ı çalıştır
                    result = agent.research_soil(query, soil_data)
                    
                    if result.get("success"):
                        # Detaylı rapor oluştur
                        report = f"🔍 ARAŞTIRMA RAPORU: {query}\n\n"
                        
                        if soil_data:
                            soil_info = soil_data.get('classification', {}).get('wrb4_description', 'Bilinmiyor')
                            report += f"📍 ANALİZ EDİLEN TOPRAK: {soil_info}\n"
                            report += f"📊 Koordinatlar: Boylam={lon}, Enlem={lat}\n\n"
                        else:
                            report += "📍 TOPRAK VERİSİ: Mevcut değil (genel bilgiler kullanıldı)\n\n"
                        
                        report += f"🛠️ Kullanılan Araçlar: {', '.join(result.get('tools_used', []))}\n\n"
                        
                        # Bulguları detaylı göster
                        findings = result.get("findings", [])
                        if findings:
                            report += "📊 BULGULAR:\n"
                            for i, finding in enumerate(findings, 1):
                                tool_name = finding.get("tool", "Bilinmeyen")
                                data = finding.get("data", {})
                                finding_type = finding.get("type", "")
                                
                                report += f"   {i}. {tool_name} ({finding_type}):\n"
                                
                                if finding_type == "soil_analysis" and isinstance(data, str):
                                    report += f"      - {data}\n"
                                
                                elif finding_type == "rag_knowledge" and isinstance(data, str):
                                    # RAG cevabını formatla
                                    lines = data.split('\n')
                                    for line in lines[:4]:  # İlk 4 satır
                                        if line.strip():
                                            report += f"      - {line.strip()}\n"
                                
                                elif finding_type == "weather_info" and isinstance(data, str):
                                    report += f"      - {data}\n"
                                
                                elif isinstance(data, dict):
                                    if 'title' in data:
                                        report += f"      - {data['title']}\n"
                                    if 'soil_requirements' in data:
                                        report += f"      - Toprak: {data['soil_requirements']}\n"
                                    if 'climate_requirements' in data:
                                        report += f"      - İklim: {data['climate_requirements']}\n"
                                    if 'soil_type' in data:
                                        report += f"      - Toprak Türü: {data['soil_type']}\n"
                                    if 'ph_level' in data:
                                        report += f"      - pH: {data['ph_level']}\n"

                        # Öneriler
                        recommendations = result.get("recommendations", [])
                        if recommendations:
                            report += "\n💡 TAVSİYELER:\n"
                            for rec in recommendations:
                                report += f"   • {rec}\n"
                        
                        return report
                    else:
                        return f"❌ Araştırma hatası: {result.get('error', 'Bilinmeyen hata')}"
                        
                except ImportError as e:
                    return f"❌ Research Agent import hatası: {e}"
                except Exception as e:
                    return f"❌ Research Agent hatası: {e}"
            
            else:
                return f"Bilinmeyen fonksiyon: {function_name}"
                
        except Exception as e:
            error_msg = f"Fonksiyon çalıştırma hatası: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def reset_conversation(self):
        """Konuşma geçmişini sıfırla"""
        self.conversation_history = []
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
        print("🔄 Konuşma geçmişi sıfırlandı")
    
    def get_conversation_history(self) -> List[Dict]:
        """Konuşma geçmişini döndür"""
        return self.conversation_history
    
    def print_history(self):
        """Konuşma geçmişini yazdır"""
        print("\n📜 Konuşma Geçmişi:")
        print("=" * 60)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "👤 Kullanıcı" if msg["role"] == "user" else "🤖 Asistan"
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{i}. {role}: {content_preview}")
        print("=" * 60)