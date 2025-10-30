# llm_handler.py
import os
import httpx
import asyncio
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Windows konum servisi için
try:
    from winsdk.windows.devices.geolocation import Geolocator, PositionStatus
    WINDOWS_GEOLOCATION_AVAILABLE = True
except ImportError:
    WINDOWS_GEOLOCATION_AVAILABLE = False
    print("⚠️  Windows Geolocation kütüphanesi kullanılamıyor. IP tabanlı konum kullanılacak.")

load_dotenv() # .env dosyasından ortam değişkenlerini yükle 

# --- 1. API Anahtarı ve LLM Kurulumu ---
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    llm_model = genai.GenerativeModel('models/gemini-2.5-flash')
except KeyError:
    print("❌ Hata: GEMINI_API_KEY ortam değişkeni bulunamadı.")
    print("Lütfen API anahtarınızı ayarlayıp tekrar deneyin.")
    exit()

# --- 2. Otomatik Konum Tespiti - GPS/Windows Konum Servisi ---
async def get_automatic_coordinates():
    """
    Windows Konum Servisi (GPS/Wi-Fi) ile otomatik konum tespiti yapar.
    """
    print("🌐 Windows Konum Servisi ile konum tespiti yapılıyor...")
    
    # Windows konum servisi mevcut değilse IP tabanlı yönteme fallback
    if not WINDOWS_GEOLOCATION_AVAILABLE:
        print("⚠️  Windows konum servisi kullanılamıyor, IP tabanlı konuma geçiliyor...")
        return await get_ip_based_coordinates()
    
    try:
        print("📍 Konum servisine erişim isteniyor...")
        access_status = await Geolocator.request_access_async()

        if access_status == 0:  # Denied
            print("❌ Konum izni reddedildi. IP tabanlı konuma geçiliyor...")
            print("   📍 Ayarlar > Gizlilik > Konum'dan izin verebilirsiniz.")
            return await get_ip_based_coordinates()
        elif access_status == 3:  # Unspecified error
            print("❌ Konum servisinde hata. IP tabanlı konuma geçiliyor...")
            return await get_ip_based_coordinates()
        elif access_status == 2:  # NotDetermined
            print("ℹ️  Lütfen açılan pencereden konum iznini onaylayın...")

        print("📍 Konum bilgisi alınıyor...")
        geolocator = Geolocator()
        
        # Konum bilgisini al
        pos = await geolocator.get_geoposition_async()
        coord = pos.coordinate
        
        lat = coord.point.position.latitude
        lon = coord.point.position.longitude
        accuracy = coord.accuracy
        
        print(f"✅ Windows Konum Servisi - Konum tespit edildi")
        print(f"📍 Koordinatlar: Boylam={lon:.6f}, Enlem={lat:.6f}")
        print(f"🎯 Doğruluk: {accuracy} metre")
        print("💡 Not: Bu konum GPS/Wi-Fi/hücresel ağ ile tespit edilmiştir")
        
        return lon, lat
        
    except Exception as e:
        print(f"❌ Windows konum servisi hatası: {e}")
        print("🔄 IP tabanlı konuma geçiliyor...")
        return await get_ip_based_coordinates()

async def get_ip_based_coordinates():
    """
    IP adresinden yedek konum tespiti (Windows konum servisi başarısız olursa)
    """
    print("🌐 IP tabanlı konum tespiti yapılıyor...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ip-api.com/json/", timeout=10.0)
            
            if response.status_code == 200:
                location_data = response.json()
                
                if location_data.get("status") == "success":
                    lat = location_data.get("lat")
                    lon = location_data.get("lon")
                    city = location_data.get("city", "Bilinmeyen")
                    country = location_data.get("country", "Bilinmeyen")
                    
                    print(f"✅ IP tabanlı konum tespit edildi: {city}, {country}")
                    print(f"📍 Koordinatlar: Boylam={lon}, Enlem={lat}")
                    print("💡 Not: Bu konum IP adresinize dayalı bir tahmindir (daha az hassas)")
                    return lon, lat
                else:
                    print("❌ IP tabanlı konum tespit edilemedi.")
                    return None, None
            else:
                print("❌ IP konum servisine erişilemedi.")
                return None, None
                
    except httpx.RequestError:
        print("❌ İnternet bağlantısı yok veya konum servisi ulaşılamıyor.")
        return None, None
    except Exception as e:
        print(f"❌ IP konum tespit hatası: {e}")
        return None, None

# --- 3. Kullanıcıdan Koordinat Alma ---
def get_coordinates_from_user():
    """
    Kullanıcıdan manuel olarak koordinatları alır.
    """
    print("\n📍 Manuel Koordinat Girişi")
    print("-" * 25)
    
    try:
        longitude = float(input("Boylam (Longitude) girin (-180 ile 180 arası): "))
        latitude = float(input("Enlem (Latitude) girin (-90 ile 90 arası): "))
        
        # Koordinat sınırlarını kontrol et
        if not (-180 <= longitude <= 180):
            print("❌ Hata: Boylam -180 ile 180 arasında olmalıdır.")
            return None, None
        
        if not (-90 <= latitude <= 90):
            print("❌ Hata: Enlem -90 ile 90 arasında olmalıdır.")
            return None, None
        
        print(f"✅ Koordinatlar alındı: Boylam={longitude}, Enlem={latitude}")
        return longitude, latitude
        
    except ValueError:
        print("❌ Hata: Geçerli bir sayı giriniz.")
        return None, None
    except KeyboardInterrupt:
        print("\n👋 İşlem iptal edildi.")
        return None, None

# --- 4. Soil API İsteği (Koordinat -> Toprak Verisi) ---
async def get_soil_data(longitude: float, latitude: float):
    """
    Çalışan Soil API'ye istek atarak toprak verisini çeker.
    """
    # Doğru endpoint
    api_url = "http://localhost:8000/soiltype/analyze"
    
    # Doğru JSON formatı - ONDALIKLI koordinatlar
    request_data = {
        "method": "Manual",
        "longitude": longitude,  # ONDALIKLI
        "latitude": latitude     # ONDALIKLI
    }
    
    print(f"🛰️ Soil API'ye istek gönderiliyor: {api_url}")
    print(f"📤 Gönderilen JSON: {json.dumps(request_data, ensure_ascii=False)}")
    print(f"📍 Koordinatlar: Boylam={longitude}, Enlem={latitude}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=request_data, timeout=30.0)
            
            if response.status_code == 200:
                print("✅ API'den başarılı yanıt alındı.")
                soil_data = response.json()
                print(f"📊 Alınan veri: Soil ID {soil_data.get('soil_id', 'Bilinmiyor')}")
                return soil_data
            elif response.status_code == 404:
                print("❌ API'den 404 alındı: Bu koordinatlarda veri bulunamadı.")
                return {"error": "Soil data not found for these coordinates."}
            else:
                print(f"❌ API Hatası: {response.status_code}")
                print(f"   Mesaj: {response.text}")
                return {"error": f"API Error: {response.status_code}", "details": response.text}
                
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! Soil API'nin çalıştığından emin misiniz?")
            print("   Soil API'yi başlatmak için: python -m uvicorn soil_api:app --reload")
            return {"error": "Connection failed. Is the Soil API running?"}
        except httpx.ReadTimeout:
            print("⏰ Zaman aşımı! Soil API yanıt vermiyor.")
            return {"error": "Request timeout. Soil API might be overloaded."}
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

# --- 4.1. Soil API İsteği - Otomatik Konum Tespiti ---
async def get_soil_data_auto():
    """
    Otomatik konum tespiti için Soil API'ye istek atar.
    """
    # Doğru endpoint - otomatik analiz için
    api_url = "http://localhost:8000/soiltype/analyze/auto"
    
    # Doğru JSON formatı - otomatik analiz için
    request_data = {
        "method": "Auto"
    }
    
    print(f"🛰️ Soil API'ye OTOMATİK analiz isteği gönderiliyor: {api_url}")
    print(f"📤 Gönderilen JSON: {json.dumps(request_data, ensure_ascii=False)}")
    print("📍 Koordinatlar: Otomatik tespit edilecek")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=request_data, timeout=30.0)
            
            if response.status_code == 200:
                print("✅ API'den başarılı yanıt alındı.")
                soil_data = response.json()
                print(f"📊 Alınan veri: Soil ID {soil_data.get('soil_id', 'Bilinmiyor')}")
                
                # Otomatik analizde koordinatları response'tan al
                if 'coordinates' in soil_data:
                    coords = soil_data['coordinates']
                    print(f"📍 API tarafından tespit edilen koordinatlar: Boylam={coords.get('longitude')}, Enlem={coords.get('latitude')}")
                
                return soil_data
            elif response.status_code == 404:
                print("❌ API'den 404 alındı: Otomatik konum tespiti başarısız veya bu konumda veri bulunamadı.")
                return {"error": "Automatic location detection failed or no soil data found."}
            else:
                print(f"❌ API Hatası: {response.status_code}")
                print(f"   Mesaj: {response.text}")
                return {"error": f"API Error: {response.status_code}", "details": response.text}
                
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! Soil API'nin çalıştığından emin misiniz?")
            print("   Soil API'yi başlatmak için: python -m uvicorn main:app --reload")
            return {"error": "Connection failed. Is the Soil API running?"}
        except httpx.ReadTimeout:
            print("⏰ Zaman aşımı! Soil API yanıt vermiyor.")
            return {"error": "Request timeout. Soil API might be overloaded."}
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

# --- 5. RAG - LLM Cevap Üretimi (Veri -> Doğal Dil) ---
def generate_llm_answer(coordinates: tuple, soil_json: dict, location_method: str):
    """
    Toprak verisini alıp LLM'e (Gemini) gönderir.
    """
    print("🧠 Gemini modeli ile cevap üretiliyor...")
    
    lon, lat = coordinates
    
    # Eğer API hatası geldiyse, hatayı doğrudan LLM'e bildir
    if "error" in soil_json:
        prompt = f"""
        Kullanıcı koordinatlar için toprak analizi istedi, ancak veritabanından veri çekerken
        bir hata oluştu. Lütfen bu hatayı kullanıcıya nazikçe açıklayın.

        Konum Yöntemi: {location_method}
        İstenen Koordinatlar:
        - Boylam: {lon}
        - Enlem: {lat}

        Alınan Hata: {json.dumps(soil_json, indent=2, ensure_ascii=False)}
        """
    else:
        # Başarılı veri alımı
        prompt = f"""
        GÖREV: Sen bir toprak bilimi uzmanısın. Aşağıdaki teknik JSON
        verisini kullanarak belirtilen koordinatlardaki toprak analizini
        doğal, akıcı ve anlaşılır bir dille açıkla.

        KONUM YÖNTEMİ: {location_method}
        ANALİZ KOORDİNATLARI:
        - Boylam: {lon}
        - Enlem: {lat}

        TEKNİK TOPRAK ANALİZ VERİSİ (JSON):
        {json.dumps(soil_json, indent=2, ensure_ascii=False)}

        CEVAP TALİMATLARI:
        1.  Cevaba, analizin hangi koordinatlar için yapıldığını ve konumun nasıl belirlendiğini belirterek başla.
        2.  Toprak sınıflandırmasını (classification.wrb4_description) açıkla.
        3.  Temel özelliklerden (basic_properties) pH ve Organik Karbon'u belirt.
        4.  Doku özelliklerinden (texture_properties) kil, silt ve kum oranlarını belirt.
        5.  Teknik terimleri (örn: "CMca") açıklayarak kullan.
        6.  Cevabı teknik bir rapor gibi değil, bir uzmanın açıklaması gibi sun.
        """
    
    try:
        response = llm_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ LLM üretimi sırasında hata: {e}")
        return "Cevap üretirken bir sorunla karşılaştım."

# --- 6. Ana Çalıştırıcı ---
async def main():
    print("🤖 LLM Toprak Analizi Asistanı")
    print("=" * 50)
    print("Bu program, otomatik konum tespiti veya manuel koordinat")
    print("girişi ile toprak analizi yapar.")
    print("Çıkmak için menüde 'çıkış' seçeneğini kullanabilirsiniz.")
    print("\n📍 Özellikler:")
    print("   - 🌐 Otomatik konum tespiti (Windows GPS/Konum Servisi)")
    print("   - 📍 Manuel koordinat girişi")
    print("   - 🌍 Detaylı toprak analizi")
    print("-" * 50)
    
    while True:
        try:
            print("\n" + "=" * 50)
            print("🌍 ANALİZ YÖNTEMİ SEÇİN")
            print("=" * 50)
            print("1. 🌐 Otomatik Konum Tespiti (GPS/Wi-Fi)")
            print("2. 📍 Manuel Koordinat Girişi")
            print("3. 👋 Çıkış")
            print("-" * 50)
            
            choice = input("Seçiminiz (1-3): ").strip()
            
            if choice == '3' or choice.lower() in ['çıkış', 'exit', 'quit']:
                print("👋 Görüşmek üzere!")
                break
            elif choice == '1':
                # Otomatik konum tespiti - Windows GPS/Konum Servisi
                lon, lat = await get_automatic_coordinates()
                location_method = "Otomatik konum tespiti (Windows Konum Servisi)"
                
                if lon is None or lat is None:
                    print("\n❌ Otomatik konum tespiti başarısız.")
                    print("   Lütfen manuel koordinat girişini deneyin.")
                    continue
                
                # Otomatik analiz fonksiyonunu kullan
                soil_data = await get_soil_data_auto()
                    
            elif choice == '2':
                # Manuel koordinat girişi
                print("\n" + "=" * 30)
                print("Manuel koordinat girişi için örnekler:")
                print("   - Konya: Boylam=32.5, Enlem=37.8")
                print("   - Ankara: Boylam=32.8, Enlem=39.9") 
                print("   - İstanbul: Boylam=28.97, Enlem=41.01")
                print("   - İzmir: Boylam=27.14, Enlem=38.42")
                print("=" * 30)
                
                lon, lat = get_coordinates_from_user()
                location_method = "Manuel koordinat girişi"
                
                if lon is None or lat is None:
                    continue
                
                # Manuel analiz için normal fonksiyonu kullan
                soil_data = await get_soil_data(lon, lat)
            else:
                print("❌ Geçersiz seçim! Lütfen 1, 2 veya 3 girin.")
                continue
            
            # LLM cevabı
            final_answer = generate_llm_answer((lon, lat), soil_data, location_method)
            
            print("\n" + "=" * 60)
            print("🌍 TOPRAK ANALİZ SONUCU")
            print("=" * 60)
            print(f"📍 Yöntem: {location_method}")
            print(f"📊 Koordinatlar: Boylam={lon}, Enlem={lat}")
            print("=" * 60)
            print(final_answer)
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n👋 Görüşmek üzere!")
            break

if __name__ == "__main__":
    print("--- LLM Toprak Analiz Sistemi Başlatıldı ---")
    print("İPUCU: Bu scripti çalıştırmadan önce Soil API sunucunuzun çalışır durumda olduğundan emin olun.")
    print("Soil API'yi başlatmak için: python -m uvicorn main:app --reload")
    
    if WINDOWS_GEOLOCATION_AVAILABLE:
        print("\n📍 ÖZELLİK: Windows Konum Servisi aktif (GPS/Wi-Fi konum tespiti)")
    else:
        print("\n⚠️  UYARI: Windows Konum Servisi kullanılamıyor, IP tabanlı konum kullanılacak")
        print("   📍 'pip install winsdk' komutu ile Windows konum servisini etkinleştirebilirsiniz")
    
    asyncio.run(main())