# main_chatbot.py - Chatbot Ana Dosyası
import os
import sys
import asyncio
import importlib.util
from pathlib import Path
import atexit
import subprocess
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn
import re
from typing import Optional

# Çıkışta API süreçlerini durdur
api_process = None

# Global chatbot instance
chatbot_instance = None
service_manager_instance = None

# FastAPI app for frontend communication
app = FastAPI(
    title="UMAY Chatbot API",
    version="1.0.0",
    description="Chatbot API for frontend communication"
)

# --- Yol Konfigürasyonu ---
class PathConfig:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")
    FRONTEND_STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
    BACKEND_API = os.path.join(BASE_DIR, "Backend", "API")
    BACKEND_SOIL_API = os.path.join(BACKEND_API, "SoilType")
    BACKEND_RAG = os.path.join(BASE_DIR, "Backend", "RAG")
    LLM_DIR = os.path.join(BASE_DIR, "LLM")
    AGENTS_DIR = os.path.join(LLM_DIR, "agents")
    CHAINS_DIR = os.path.join(LLM_DIR, "chains")
    TOOLS_DIR = os.path.join(LLM_DIR, "tools")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend için
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Serve Frontend static files under /static
app.mount("/static", StaticFiles(directory=PathConfig.FRONTEND_STATIC_DIR), name="static")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    conversation_id: int = 0
    user_location: Optional[dict] = None

class ChatResponse(BaseModel):
    success: bool
    response: str = ""
    error: str = ""
    timestamp: float
    conversation_id: int

# Yolları Python path'ine ekle
sys.path.extend([
    PathConfig.BASE_DIR,
    PathConfig.BACKEND_SOIL_API,
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

# --- Service Manager'ı import et ---
try:
    # Önce main.py'nin bulunduğu dizini ekle
    main_dir = os.path.dirname(PathConfig.BASE_DIR)
    if main_dir not in sys.path:
        sys.path.insert(0, main_dir)
    
    from main import UmayServiceManager
    print("✅ Service Manager başarıyla import edildi")
except ImportError as e:
    print(f"❌ Service Manager import hatası: {e}")
    print("💡 main.py dosyasının doğru konumda olduğundan emin olun")
    exit(1)

# --- ChatBot'u import et ---
try:
    chatbot_path = os.path.join(PathConfig.LLM_DIR, "chatbot.py")
    spec = importlib.util.spec_from_file_location("chatbot", chatbot_path)
    chatbot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chatbot_module)
    OrganicFarmingChatBot = chatbot_module.OrganicFarmingChatBot
    print("✅ ChatBot modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ ChatBot modülü yüklenemedi: {e}")
    print("💡 chatbot.py dosyasını LLM/ dizinine kopyalayın")
    exit(1)

async def start_soil_api():
    """API server'ını otomatik başlat (Soil + Weather)"""
    global api_process
    
    try:
        # API'nin çalışıp çalışmadığını kontrol et
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/docs", timeout=2.0)
            if response.status_code == 200:
                print("✅ Soil+Weather API zaten çalışıyor!")
                return True
    except:
        pass  # API çalışmıyor, başlatacağız
    
    # API'yi başlat
    try:
        # API dizinine git
        api_dir = PathConfig.BACKEND_API
        
        # Virtual environment Python'u kullan
        base_dir = PathConfig.BASE_DIR
        env_python = os.path.join(base_dir, "env", "Scripts", "python.exe")
        if not os.path.exists(env_python):
            print(f"❌ Virtual environment bulunamadı: {env_python}")
            return False
        
        # Uvicorn'u subprocess olarak başlat ve global değişkene kaydet
        # stdout/stderr'i DEVNULL'a yönlendir - buffer dolmasını önler ve API'lerin kapanmasını engeller
        api_process = subprocess.Popen([
            env_python, "-m", "uvicorn", 
            "main:app",
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], cwd=api_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Başlatılmasını bekle
        time.sleep(5)
        
        # Kontrol et
        async with httpx.AsyncClient() as client:
            for i in range(10):
                try:
                    response = await client.get("http://localhost:8000/docs", timeout=10.0)
                    if response.status_code == 200:
                        print("✅ Soil+Weather API başarıyla başlatıldı!")
                        return True
                    else:
                        print(f"⏳ Soil+Weather API yükleniyor... Deneme {i+1}/10")
                except Exception as e:
                    print(f"⏳ Soil+Weather API başlatılıyor... Deneme {i+1}/10 - {e}")
                
                time.sleep(3)
        
        print("❌ Soil+Weather API başlatılamadı!")
        return False
    except Exception as e:
        print(f"❌ Soil+Weather API başlatma hatası: {e}")
        return False
async def start_ml_api():
    """ML API server'ını otomatik başlat (8003)."""
    try:
        # Çalışıyor mu?
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get("http://localhost:8003/ml/health", timeout=2.0)
                if r.status_code == 200:
                    print("✅ ML API zaten çalışıyor!")
                    return True
            except Exception:
                pass

        # Başlat
        base_dir = PathConfig.BASE_DIR
        env_python = os.path.join(base_dir, "env", "Scripts", "python.exe")
        ml_dir = os.path.join(base_dir, "Backend", "API", "MachineLearning")
        if not os.path.exists(env_python):
            print(f"❌ Virtual environment bulunamadı: {env_python}")
            return False

        # stdout/stderr'i DEVNULL'a yönlendir - buffer dolmasını önler ve API'lerin kapanmasını engeller
        proc = subprocess.Popen([
            env_python, "ml_api.py"
        ], cwd=ml_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Yükselebilmesi için bekle
        import time
        time.sleep(3)

        # Kontrol et
        async with httpx.AsyncClient() as client:
            for i in range(10):
                try:
                    r = await client.get("http://localhost:8003/ml/health", timeout=5.0)
                    if r.status_code == 200:
                        print("✅ ML API başarıyla başlatıldı!")
                        return True
                except Exception as e:
                    print(f"⏳ ML API yükleniyor... Deneme {i+1}/10 - {e}")
                time.sleep(1)
        print("❌ ML API başlatılamadı!")
        return False
    except Exception as e:
        print(f"❌ ML API başlatma hatası: {e}")
        return False


def cleanup_apis():
    """Uygulama kapatıldığında tüm API'leri kapat"""
    global api_process
    print("🔴 Tüm API'ler kapatılıyor...")
    try:
        if api_process:
            api_process.terminate()
        
        # subprocess'leri temizle
        import os
        os.system("taskkill /F /IM uvicorn.exe >nul 2>&1")
        os.system("taskkill /F /IM python.exe >nul 2>&1")
        print("✅ Tüm API'ler kapatıldı")
    except Exception as e:
        print(f"⚠️ API kapatılırken hata: {e}")

# Uygulama kapatıldığında cleanup_apis fonksiyonunu çağır
atexit.register(cleanup_apis)

# API Endpoints and Frontend serving
@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the Frontend index.html at root so UI loads on 8001 with cache-busting"""
    index_path = os.path.join(PathConfig.FRONTEND_DIR, "index.html")
    
    # HTML dosyasını oku
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Cache-busting için timestamp
    timestamp = int(time.time())
    cache_param = f"?v={timestamp}"
    
    # CSS ve JS dosya URL'lerine cache-busting parametresi ekle
    # CSS dosyası için - mevcut query parametresi varsa değiştir, yoksa ekle
    html_content = re.sub(
        r'(href=["\']static/css/[^"\']+\.css)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    # JS dosyası için - mevcut query parametresi varsa değiştir, yoksa ekle
    html_content = re.sub(
        r'(src=["\']static/js/[^"\']+\.js)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    return HTMLResponse(content=html_content)

@app.get("/login.html", response_class=HTMLResponse)
def login():
    """Serve the Frontend login.html with cache-busting"""
    login_path = os.path.join(PathConfig.FRONTEND_DIR, "login.html")
    
    # HTML dosyasını oku
    with open(login_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Cache-busting için timestamp
    timestamp = int(time.time())
    cache_param = f"?v={timestamp}"
    
    # CSS ve JS dosya URL'lerine cache-busting parametresi ekle
    html_content = re.sub(
        r'(href=["\']static/css/[^"\']+\.css)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    html_content = re.sub(
        r'(src=["\']static/js/[^"\']+\.js)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    return HTMLResponse(content=html_content)

@app.get("/register.html", response_class=HTMLResponse)
def register_page():
    """Serve the Frontend register.html with cache-busting"""
    register_path = os.path.join(PathConfig.FRONTEND_DIR, "register.html")
    
    # HTML dosyasını oku
    with open(register_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Cache-busting için timestamp
    timestamp = int(time.time())
    cache_param = f"?v={timestamp}"
    
    # CSS ve JS dosya URL'lerine cache-busting parametresi ekle
    html_content = re.sub(
        r'(href=["\']static/css/[^"\']+\.css)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    html_content = re.sub(
        r'(src=["\']static/js/[^"\']+\.js)(\?v=\d+)?(["\'])',
        rf'\1{cache_param}\3',
        html_content
    )
    
    return HTMLResponse(content=html_content)

@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(PathConfig.FRONTEND_DIR, "manifest.json"))

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "UMAY Chatbot API"}

async def main():
    """Ana fonksiyon - Sadece Web API modu"""
    
    print("""🌱 UMAY TARIM ASİSTANI 🌱""")
    
    await run_web_api()

async def run_web_api():
    """Web API modu - Frontend için"""
    print("🌐 Web API Modu başlatılıyor...")
    
    # Chatbot'u başlat (input beklemeden)
    await initialize_chatbot()
    
    if not chatbot_instance:
        print("❌ Chatbot başlatılamadı!")
        return
    
    print("\n🚀 Web API sunucusu başlatılıyor...")
    print("🔗 Chatbot API: http://localhost:8001")
    print("🌱 Soil+Weather API: http://localhost:8000")
    print("📚 Docs: http://localhost:8001/docs")
    print("\n⏹️ Durdurmak için Ctrl+C")
    
    # Web API'yi başlat
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def initialize_chatbot():
    """Chatbot'u başlat (input beklemeden)"""
    global chatbot_instance, service_manager_instance
    
    # ✅ 1. SOIL+WEATHER API'Yİ BAŞLAT
    soil_api_started = await start_soil_api()
    if not soil_api_started:
        print("❌ Soil+Weather API olmadan devam edilemez!")
        return False

    # ✅ 2. ML API'Yİ BAŞLAT
    ml_api_started = await start_ml_api()
    if not ml_api_started:
        print("❌ ML API olmadan devam edilemez!")
        return False
    
    # Service Manager'ı başlat
    print("\n🔧 Servisler başlatılıyor...")
    service_manager = UmayServiceManager()
    await service_manager.initialize_services()
    service_manager_instance = service_manager
    
    print("\n✅ Tüm servisler hazır!")
    
    # ChatBot'u başlat
    print("\n🤖 Chatbot başlatılıyor...")
    try:
        chatbot = OrganicFarmingChatBot(
            service_manager=service_manager,
            model_name="models/gemini-2.5-flash"
        )
        chatbot_instance = chatbot
        print("✅ ChatBot başarıyla başlatıldı!")
        return True
    except Exception as e:
        print(f"❌ ChatBot başlatma hatası: {e}")
        return False

# Chat endpoint for frontend
@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Frontend'den gelen chat mesajlarını işle"""
    try:
        if not chatbot_instance:
            return ChatResponse(
                success=False,
                error="Chatbot henüz başlatılmadı",
                timestamp=time.time(),
                conversation_id=request.conversation_id
            )
        
        # Chatbot'a mesaj gönder (async olarak)
        response = await chatbot_instance.chat_async(request.message)
        
        return ChatResponse(
            success=True,
            response=response,
            timestamp=time.time(),
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        print(f"❌ Chat endpoint hatası: {e}")
        return ChatResponse(
            success=False,
            error=str(e),
            timestamp=time.time(),
            conversation_id=request.conversation_id
        )

# Weather endpoint for frontend
@app.post("/weather/")
async def weather_endpoint(request: dict):
    """Frontend'den gelen hava durumu isteklerini işle"""
    try:
        import httpx
        
        # Backend Weather API'ye otomatik konum ile istek gönder
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/weather/dailyweather/auto",
                json={
                    "method": "Auto"
                },
                params={"days": 1},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # İlk günün verilerini al
                    daily_data = data[0]
                    return {
                        "temperature": daily_data.get('temperature_2m_mean'),
                        "weather_code": daily_data.get('weather_code'),
                        "rain_sum": daily_data.get('rain_sum'),
                        "showers_sum": daily_data.get('showers_sum'),
                        "snowfall_sum": daily_data.get('snowfall_sum'),
                        "apparent_temperature_min": daily_data.get('apparent_temperature_min'),
                        "apparent_temperature_mean": daily_data.get('apparent_temperature_mean'),
                        "apparent_temperature_max": daily_data.get('apparent_temperature_max'),
                        "precipitation_sum": daily_data.get('precipitation_sum'),
                        "wind_speed_max": daily_data.get('wind_speed_10m_max'),
                        "wind_gusts_max": daily_data.get('wind_gusts_10m_max'),
                        "sunshine_duration": daily_data.get('sunshine_duration')
                    }
                else:
                    return {"error": "Hava durumu verisi alınamadı"}
            else:
                return {"error": f"API Error: {response.status_code}"}
        
    except Exception as e:
        print(f"❌ Weather endpoint hatası: {e}")
        return {"error": f"Weather verisi alınamadı: {str(e)}"}

# Soil endpoint for frontend
@app.post("/soil/")
async def soil_endpoint(request: dict):
    """Frontend'den gelen toprak analizi isteklerini işle"""
    try:
        import httpx
        
        # Backend Soil API'ye otomatik konum ile istek gönder
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/soiltype/analyze/auto",
                json={
                    "method": "Auto"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                soil_data = response.json()
                
                # Gerçek toprak analizi verilerini döndür
                classification = soil_data.get('classification', {})
                basic_props = soil_data.get('basic_properties', [])
                texture_props = soil_data.get('texture_properties', [])
                physical_props = soil_data.get('physical_properties', [])
                chemical_props = soil_data.get('chemical_properties', [])
                salinity_props = soil_data.get('salinity_properties', [])
                
                # Tüm özellikleri birleştir
                all_properties = basic_props + texture_props + physical_props + chemical_props + salinity_props
                
                # Geçerli değerleri filtrele ve formatla
                valid_properties = {}
                for prop in all_properties:
                    name = prop.get('name', '')
                    value = prop.get('value')
                    unit = prop.get('unit', '')
                    
                    # Null, -9, None değerleri filtrele
                    if value is not None and value != -9 and value != -9.0 and str(value).lower() not in ['na', 'n/a', 'null']:
                        # Sayısal değerleri 2 ondalık basamakla yuvarla
                        if isinstance(value, (int, float)):
                            formatted_value = f"{round(float(value), 2)}"
                        else:
                            formatted_value = str(value)
                        
                        # Birim varsa ekle
                        if unit:
                            valid_properties[name] = f"{formatted_value} {unit}"
                        else:
                            valid_properties[name] = formatted_value
                
                # Toprak tipi bilgileri
                # wrb4_description boşsa wrb2_description'a düş
                soil_type = classification.get('wrb4_description') or classification.get('wrb2_description') or 'Bilinmiyor'
                # wrb4_code yoksa wrb2_code'a düş
                soil_code = classification.get('wrb4_code') or classification.get('wrb2_code') or 'N/A'
                
                # Temel bilgileri ekle
                result = {
                    "soil_type": soil_type,
                    "soil_code": soil_code,
                    "description": f"Toprak ID: {soil_data.get('soil_id', 'N/A')}",
                    **valid_properties  # Tüm geçerli özellikleri ekle
                }
                
                return result
            else:
                return {"error": f"API Error: {response.status_code}"}
        
    except Exception as e:
        print(f"❌ Soil endpoint hatası: {e}")
        return {"error": f"Toprak analizi yapılamadı: {str(e)}"}


# Uvicorn server'ı başlat
def start_server():
    """FastAPI server'ı başlat"""
    print("\n🚀 FastAPI server başlatılıyor...")
    print("🌐 Frontend: http://localhost:8001")
    print("📡 API: http://localhost:8001/chat/")
    print("🌱 Mahsul Önerisi: http://localhost:8001/crop-recommendation/")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

if __name__ == "__main__":
    try:
        # Önce servisleri başlat
        asyncio.run(main())
        
        # Sonra FastAPI server'ı başlat
        start_server()
        
    except KeyboardInterrupt:
        print("\n\n👋 Program kapatılıyor...")
    except Exception as e:
        print(f"\n💥 Kritik hata: {e}")
        import traceback
        traceback.print_exc()