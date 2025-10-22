# main_chatbot.py - Chatbot Ana Dosyası
import os
import sys
import asyncio
import importlib.util
from pathlib import Path
import atexit
import subprocess
import time

# Çıkışta API sürecini durdur
api_process = None

# --- Yol Konfigürasyonu ---
class PathConfig:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BACKEND_API = os.path.join(BASE_DIR, "Backend", "API", "SoilType")
    BACKEND_RAG = os.path.join(BASE_DIR, "Backend", "RAG")
    LLM_DIR = os.path.join(BASE_DIR, "LLM")
    AGENTS_DIR = os.path.join(LLM_DIR, "agents")
    CHAINS_DIR = os.path.join(LLM_DIR, "chains")
    TOOLS_DIR = os.path.join(LLM_DIR, "tools")

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
        
        # Uvicorn'u subprocess olarak başlat ve global değişkene kaydet
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
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

async def run_chatbot():
    """Chatbot'u başlat ve çalıştır"""
    
    print("🌱 Aidea Tarım Asistanı")
    print("=" * 60)

    # SOIL API'Yİ BAŞLAT
    api_started = await start_soil_api()
    if not api_started:
        print("❌ Soil API olmadan devam edilemez!")
        return
    
    print("Organik tarım, toprak analizi ve hava durumu asistanınız!")
    print("=" * 60)
    
    # Service Manager'ı başlat
    print("\n🔧 Servisler başlatılıyor...")
    service_manager = AideaServiceManager()
    await service_manager.initialize_services()
    
    print("\n✅ Tüm servisler hazır!")
    
    # ChatBot'u başlat
    print("\n🤖 Chatbot başlatılıyor...")
    try:
        chatbot = OrganicFarmingChatBot(
            service_manager=service_manager,
            model_name="models/gemini-2.5-flash"
        )
        print("✅ ChatBot başarıyla başlatıldı!")
    except Exception as e:
        print(f"❌ ChatBot başlatma hatası: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🎯 ChatBot hazır! Soru sormaya başlayabilirsiniz.")
    print("=" * 60)
    print("\n💡 Örnek sorular:")
    print("  • 'Ankara'da bugün hava nasıl?'")
    print("  • 'Konya için toprak analizi yap (32.5, 37.8)'")
    print("  • 'Organik kompost nasıl yapılır?'")
    print("  • 'Bulunduğum yerdeki toprakta hangi ürünler yetişir?'")
    print("\n📋 Komutlar:")
    print("  • 'geçmiş' - Konuşma geçmişini göster")
    print("  • 'sıfırla' - Konuşmayı yeniden başlat")
    print("  • 'yardım' - Yardım mesajını göster")
    print("  • 'çıkış' - Programdan çık")
    print("=" * 60)
    
    # Ana chat loop
    while True:
        try:
            print("\n" + "-" * 60)
            user_input = input("👤 Siz: ").strip()
            
            if not user_input:
                continue
            
            # Özel komutlar
            if user_input.lower() in ['çıkış', 'exit', 'quit', 'q']:
                print("👋 Görüşmek üzere! İyi günler.")
                break
            
            elif user_input.lower() in ['geçmiş', 'history']:
                chatbot.print_history()
                continue
            
            elif user_input.lower() in ['sıfırla', 'reset', 'yeni']:
                chatbot.reset_conversation()
                print("🔄 Yeni konuşma başlatıldı!")
                continue
            
            elif user_input.lower() in ['yardım', 'help', '?']:
                print("\n📖 Yardım:")
                print("  • Doğal dilde soru sorun")
                print("  • Koordinatları ondalıklı girin (32.5, 37.8)")
                print("  • 'geçmiş' - Konuşma geçmişi")
                print("  • 'sıfırla' - Yeni konuşma")
                print("  • 'çıkış' - Programı kapat")
                continue
            
            # ChatBot'a gönder
            print("\n🤖 Asistan: ", end="", flush=True)
            response = await chatbot.chat_async(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Programdan çıkılıyor...")
            break
        except Exception as e:
            print(f"\n❌ Hata: {e}")
            print("💡 Tekrar deneyin veya 'yardım' yazın")

async def main():
    """Ana fonksiyon"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              🌱 AIDEA TARIM ASİSTANI 🌱                  ║
║                                                          ║
║  Organik Tarım | Toprak Analizi | Hava Durumu          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n📋 Mod Seçin:")
    print("  1. 💬 Normal Chatbot Modu")
    print("  2. 🚪 Çıkış")
    
    choice = input("\nSeçiminiz (1-2): ").strip()
    
    if choice == '1':
        await run_chatbot()
    elif choice == '2':
        print("👋 Görüşmek üzere!")
    else:
        print("❌ Geçersiz seçim! Lütfen 1 veya 2 girin.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Program kapatılıyor...")
    except Exception as e:
        print(f"\n💥 Kritik hata: {e}")
        import traceback
        traceback.print_exc()