# chatbot.py - Gemini Function Calling ile Multi-Tool ChatBot
import os
import json
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
            service_manager: AideaServiceManager instance
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
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
        
        print(f"✅ ChatBot başlatıldı: {model_name}")
        print(f"🔧 {len(self.tools)} tool tanımlandı")
    
    def _create_function_declarations(self):
        """Gemini için function declarations oluştur - DOĞRU FORMAT"""
        
        function_declarations = [
            {
                "name": "get_weather",
                "description": "Belirtilen şehir için hava durumu bilgisi getirir. Sıcaklık, nem ve genel durum bilgisi döner.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "city": {
                            "type": "STRING",
                            "description": "Türkiye'deki şehir adı (örn: İstanbul, Ankara, İzmir, Konya)"
                        }
                    },
                    "required": ["city"]
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
        """Chatbot için system prompt"""
        return """Sen Türk çiftçilere yardımcı olan organik tarım uzmanı bir asistansın. Adın "Aidea Tarım Asistanı".

🎯 GÖREVIN:
- Toprak analizi yaparak çiftçilere tarımsal öneriler sunmak
- Hava durumu bilgisi sağlamak
- Organik tarım konularında bilgi vermek
- Kullanıcının ihtiyacına göre en uygun tool'ları kullanmak

🔧 KULLANABILECEĞIN TOOL'LAR:

1. **get_weather**: Şehir için hava durumu
   - Kullanım: Hava durumu sorularında

2. **analyze_soil**: Koordinata göre toprak analizi
   - Kullanım: Belirli bir koordinat için toprak bilgisi istendiğinde

3. **get_automatic_location_soil**: Otomatik konum tespiti ile toprak analizi
   - Kullanım: "Bulunduğum yerdeki toprak nasıl?" gibi sorularda

4. **query_organic_farming_knowledge**: Organik tarım bilgi bankası (RAG)
   - Kullanım: Organik tarım teknikleri, sertifikasyon, kompost vs. sorularında

5. **comprehensive_soil_analysis**: Kapsamlı toprak raporu (Chain)
   - Kullanım: Detaylı toprak analizi istendiğinde

6. **research_agent_query**: Akıllı araştırma agent'ı
   - Kullanım: Karmaşık, çok yönlü sorularda

📋 TOOL SEÇME STRATEJİSİ:

**Basit Sorular** → Tek tool:
- "Ankara'da hava nasıl?" → get_weather
- "32.5, 37.8 koordinatındaki toprak nasıl?" → analyze_soil
- "Organik gübre nasıl yapılır?" → query_organic_farming_knowledge

**Orta Seviye** → Chain kullan:
- "Bu koordinattaki toprağı detaylı analiz et" → comprehensive_soil_analysis

**Karmaşık Sorular** → Agent kullan:
- "Bulunduğum yerde hangi ürünler yetişir ve nasıl organik yetiştiririm?" → research_agent_query

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

Şimdi kullanıcıya yardımcı olmaya hazırsın! 🌱"""
    
    async def chat_async(self, user_message: str) -> str:
        """
        Kullanıcı mesajını işle ve cevap üret (async)
        
        Args:
            user_message: Kullanıcının mesajı
            
        Returns:
            Chatbot'un cevabı
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
            response = self.chat.send_message(context)
            
            # Function calling kontrolü - DÜZELTİLMİŞ YAKLAŞIM
            function_called = False
            bot_response = ""

            if (hasattr(response, 'candidates') and 
                response.candidates and 
                hasattr(response.candidates[0].content, 'parts') and 
                response.candidates[0].content.parts):
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_called = True
                        function_call = part.function_call
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
                        
                        # DOĞRU FORMAT: Function response oluştur
                        function_response_part = genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": function_result}
                            )
                        )
                        
                        # Sonucu Gemini'ye geri gönder
                        final_response = self.chat.send_message(function_response_part)
                        bot_response = final_response.text
                        break
                
                if not function_called:
                    # Function call yoksa direkt cevabı al
                    bot_response = response.text
            else:
                bot_response = response.text
            
            # Konuşma geçmişine ekle
            self.conversation_history.append({
                "role": "assistant", 
                "content": bot_response
            })
            
            # Geçmiş limitini kontrol et
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            return bot_response
            
        except Exception as e:
            error_msg = f"❌ Bir hata oluştu: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def chat(self, user_message: str) -> str:
        """Senkron chat metodu (kolaylık için)"""
        import asyncio
        return asyncio.run(self.chat_async(user_message))
    
    async def _execute_function(self, function_name: str, args: Dict) -> Any:
        """Function call'ları çalıştır"""
        
        try:
            if function_name == "get_weather":
                tool = self.service_manager.get_tool("weather_tool")
                if tool:
                    city = args.get("city", "Ankara")
                    print(f"🌤️ Hava durumu sorgulanıyor: {city}")
                    result = tool(city)
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
                    
            elif function_name == "research_agent_query":
                query = args.get("query", "")
                use_soil = args.get("use_soil_data", False)
                
                print(f"🔬 Araştırma agent'ı: {query}")
                
                soil_data = None
                if use_soil:
                    lon = args.get("longitude")
                    lat = args.get("latitude")
                    if lon and lat:
                        soil_data = await self.service_manager.soil_analysis(lon, lat)
                
                agent = self.service_manager.get_agent("research_agent")
                if agent:
                    result = agent.research_soil(query, soil_data)
                    
                    if result.get("success"):
                        report = f"🔍 Araştırma Bulguları:\n"
                        report += f"📊 {len(result.get('findings', []))} bulgular\n\n"
                        report += f"💡 Öneriler:\n"
                        for rec in result.get("recommendations", []):
                            report += f"• {rec}\n"
                        return report
                    else:
                        return f"Araştırma hatası: {result.get('error', 'Bilinmeyen hata')}"
                else:
                    return "Research agent kullanılamıyor"
            
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