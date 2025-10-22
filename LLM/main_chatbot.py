# main_chatbot.py - Chatbot Ana Dosyası
import os
import sys
import asyncio
import importlib.util
from pathlib import Path

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


async def run_chatbot():
    """Chatbot'u başlat ve çalıştır"""
    
    print("🌱 Aidea Tarım Asistanı")
    print("=" * 60)
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
            model_name="models/gemini-2.5-flash"  # Daha kararlı model
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


async def run_demo():
    """Demo mod - otomatik test sorguları"""
    
    print("🎬 DEMO MODU - Otomatik Test Sorguları")
    print("=" * 60)
    
    # Service Manager başlat
    service_manager = AideaServiceManager()
    await service_manager.initialize_services()
    
    # ChatBot başlat
    try:
        chatbot = OrganicFarmingChatBot(service_manager=service_manager)
        print("✅ Demo ChatBot başlatıldı")
    except Exception as e:
        print(f"❌ Demo ChatBot başlatma hatası: {e}")
        return
    
    # Test soruları
    demo_queries = [
        "Merhaba! Sen kimsin?",
        "Ankara'da bugün hava nasıl?",
        "32.5 boylam, 37.8 enlem koordinatındaki toprağı analiz et",
        "Organik gübre nasıl yapılır?",
        "Bulunduğum yerdeki toprak için en uygun ürünler neler?"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'='*60}")
        print(f"📝 Demo Soru {i}/{len(demo_queries)}")
        print(f"{'='*60}")
        print(f"👤 Soru: {query}")
        print(f"{'='*60}")
        
        response = await chatbot.chat_async(query)
        print(f"🤖 Cevap:\n{response}")
        
        if i < len(demo_queries):  # Son sorgudan sonra bekleme
            print("\n⏳ Bir sonraki soruya geçiliyor...")
            await asyncio.sleep(2)  # 2 saniye bekle
    
    print("\n✅ Demo tamamlandı!")


async def main():
    """Ana fonksiyon"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              🌱 AIDEA TARIM ASİSTANI 🌱                  ║
║                                                          ║
║  Organik Tarım | Toprak Analizi | Hava Durumu          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n📋 Mod Seçin:")
        print("  1. 💬 Normal Chatbot Modu")
        print("  2. 🎬 Demo Modu (Otomatik Test)")
        print("  3. 🚪 Çıkış")
        
        choice = input("\nSeçiminiz (1-3): ").strip()
        
        if choice == '1':
            await run_chatbot()
            break
        elif choice == '2':
            await run_demo()
            break
        elif choice == '3':
            print("👋 Görüşmek üzere!")
            break
        else:
            print("❌ Geçersiz seçim! Lütfen 1, 2 veya 3 girin.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Program kapatıldı.")
    except Exception as e:
        print(f"\n💥 Kritik hata: {e}")
        import traceback
        traceback.print_exc()