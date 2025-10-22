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
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Çıkışta API sürecini durdur
api_process = None

# Global chatbot instance
chatbot_instance = None
service_manager_instance = None

# FastAPI app for frontend communication
app = FastAPI(
    title="Aidea Chatbot API",
    version="1.0.0",
    description="Chatbot API for frontend communication"
)

# --- Yol Konfigürasyonu ---
class PathConfig:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")
    FRONTEND_STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
    BACKEND_API = os.path.join(BASE_DIR, "Backend", "API", "SoilType")
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
    user_location: dict = None

class ChatResponse(BaseModel):
    success: bool
    response: str = ""
    error: str = ""
    timestamp: float
    conversation_id: int

# Yolları Python path'ine ekle
sys.path.extend([
    PathConfig.BASE_DIR,
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

# --- Service Manager'ı import et ---
try:
    # Önce main.py'nin bulunduğu dizini ekle
    main_dir = os.path.dirname(PathConfig.BASE_DIR)
    if main_dir not in sys.path:
        sys.path.insert(0, main_dir)
    
    from main import AideaServiceManager
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
    """Soil API server'ını otomatik başlat"""
    global api_process
    print("🔧 Soil API server başlatılıyor...")
    
    try:
        # API'nin çalışıp çalışmadığını kontrol et
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/docs", timeout=2.0)
            if response.status_code == 200:
                print("✅ Soil API zaten çalışıyor!")
                return True
    except:
        pass  # API çalışmıyor, başlatacağız
    
    # API'yi başlat
    try:
        # API dizinine git
        api_dir = os.path.join(PathConfig.BASE_DIR, "Backend", "API")
        
        # Backend/API/env virtual environment'ını kullan
        env_python = os.path.join(api_dir, "env", "Scripts", "python.exe")
        if not os.path.exists(env_python):
            print(f"❌ Virtual environment bulunamadı: {env_python}")
            return False
        
        print(f"🔍 Virtual environment Python: {env_python}")
        
        # Uvicorn'u subprocess olarak başlat ve global değişkene kaydet
        api_process = subprocess.Popen([
            env_python, "-m", "uvicorn", 
            "main:app",
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], cwd=api_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Başlatılmasını bekle
        print("⏳ API başlatılıyor...")
        time.sleep(5)
        
        # Kontrol et
        async with httpx.AsyncClient() as client:
            for i in range(10):
                try:
                    response = await client.get("http://localhost:8000/docs", timeout=10.0)
                    if response.status_code == 200:
                        print("✅ Soil API başarıyla başlatıldı!")
                        return True
                    else:
                        print(f"⏳ API yükleniyor... Deneme {i+1}/10")
                except Exception as e:
                    print(f"⏳ API başlatılıyor... Deneme {i+1}/10 - {e}")
                
                time.sleep(3)
        
        print("❌ Soil API başlatılamadı!")
        return False
        
    except Exception as e:
        print(f"❌ API başlatma hatası: {e}")
        return False

def cleanup_api():
    """Uygulama kapatıldığında API'yi kapat"""
    global api_process
    print("🔴 Soil API kapatılıyor...")
    try:
        if api_process:
            # Sadece terminate et, wait etme
            api_process.terminate()
        # subprocess.run yerine doğrudan os.system kullan
        import os
        os.system("taskkill /F /IM uvicorn.exe >nul 2>&1")
        os.system("taskkill /F /IM python.exe >nul 2>&1")
        print("✅ Soil API kapatıldı")
    except Exception as e:
        print(f"⚠️ API kapatılırken hata: {e}")

# Uygulama kapatıldığında cleanup_api fonksiyonunu çağır
atexit.register(cleanup_api)

# API Endpoints and Frontend serving
@app.get("/")
def root():
    """Serve the Frontend index.html at root so UI loads on 8001"""
    index_path = os.path.join(PathConfig.FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(PathConfig.FRONTEND_DIR, "manifest.json"))

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "Aidea Chatbot API"}

# Eski /api/chat endpoint'i kaldırıldı - sadece /chat/ kullanılıyor

# Eski run_chatbot fonksiyonu kaldırıldı - sadece Web API modu kullanılıyor

async def main():
    """Ana fonksiyon - Sadece Web API modu"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              🌱 AIDEA TARIM ASİSTANI 🌱                  ║
║                                                          ║
║  Organik Tarım | Toprak Analizi | Hava Durumu          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("🌐 Web API Modu başlatılıyor...")
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
    print("📱 Frontend: Frontend/index.html dosyasını tarayıcıda açın")
    print("🔗 API: http://localhost:8001")
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
    
    print("🌱 Aidea Tarım Asistanı")
    print("=" * 60)

    # SOIL API'Yİ BAŞLAT
    api_started = await start_soil_api()
    if not api_started:
        print("❌ Soil API olmadan devam edilemez!")
        return False
    
    print("Organik tarım, toprak analizi ve hava durumu asistanınız!")
    print("=" * 60)
    
    # Service Manager'ı başlat
    print("\n🔧 Servisler başlatılıyor...")
    service_manager = AideaServiceManager()
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

# Root endpoint zaten yukarıda tanımlı - bu kısmı kaldırıyoruz


# Uvicorn server'ı başlat
def start_server():
    """FastAPI server'ı başlat"""
    print("\n🚀 FastAPI server başlatılıyor...")
    print("🌐 Frontend: http://localhost:8001")
    print("📡 API: http://localhost:8001/chat/")
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