#!/usr/bin/env python3
"""
Soil Analysis API Interactive Test Script
=========================================

Bu script, Soil Analysis API'sini interaktif olarak test eder.
Kullanıcıdan manuel/otomatik seçim alır ve ham JSON response'u gösterir.
"""

import httpx
import asyncio
import json
import geocoder
from typing import Dict, Any

def get_manual_coordinates():
    """Kullanıcıdan manuel koordinat alır"""
    print("\n📍 Manuel Koordinat Girişi")
    print("-" * 30)
    
    try:
        longitude = float(input("Boylam (Longitude) girin (-180 ile 180 arası): "))
        latitude = float(input("Enlem (Latitude) girin (-90 ile 90 arası): "))
        
        # Koordinat sınırlarını kontrol et
        if not (-180 <= longitude <= 180):
            raise ValueError("Boylam -180 ile 180 arasında olmalıdır")
        if not (-90 <= latitude <= 90):
            raise ValueError("Enlem -90 ile 90 arasında olmalıdır")
        
        # Koordinatları tam sayıya yuvarla
        lon_rounded = round(longitude)
        lat_rounded = round(latitude)
        
        print(f"✅ Koordinatlar alındı: Boylam={lon_rounded}, Enlem={lat_rounded}")
        return lon_rounded, lat_rounded
        
    except ValueError as e:
        print(f"❌ Geçersiz koordinat: {e}")
        return None, None
    except KeyboardInterrupt:
        print("\n❌ İşlem iptal edildi")
        return None, None

def get_automatic_coordinates():
    """IP adresi üzerinden otomatik konum bulur"""
    print("\n🌐 Otomatik Konum Tespiti")
    print("-" * 30)
    print("Konumunuz algılanıyor... (Bu işlem biraz sürebilir)")
    
    try:
        g = geocoder.ip('me')
        if g.ok:
            lat, lon = g.latlng
            # Koordinatları tam sayıya yuvarla
            lat_rounded = round(lat)
            lon_rounded = round(lon)
            print(f"✅ Konum algılandı: Enlem={lat_rounded}, Boylam={lon_rounded}")
            print("(Not: Bu konum, IP adresinize dayalı bir tahmindir.)")
            print("(Koordinatlar tam sayı formatında yuvarlanmıştır.)")
            return lon_rounded, lat_rounded
        else:
            print("❌ Konumunuz otomatik olarak algılanamadı.")
            return None, None
    except Exception as e:
        print(f"❌ Otomatik konum tespiti hatası: {e}")
        return None, None

def get_user_choice():
    """Kullanıcıdan analiz yöntemi seçimini alır"""
    print("\n🌍 Soil Analysis API Test")
    print("=" * 40)
    print("Analiz yöntemini seçin:")
    print("1. Manuel koordinat girişi")
    print("2. Otomatik konum tespiti")
    print("3. Çıkış")
    
    while True:
        try:
            choice = input("\nSeçiminiz (1-3): ").strip()
            
            if choice == "1":
                return "manual"
            elif choice == "2":
                return "auto"
            elif choice == "3":
                return "exit"
            else:
                print("❌ Geçersiz seçim! Lütfen 1, 2 veya 3 girin.")
        except KeyboardInterrupt:
            print("\n❌ İşlem iptal edildi")
            return "exit"

async def test_manual_analysis(longitude, latitude):
    """Manuel koordinat analizi testi"""
    print(f"\n🧪 Manuel Analiz Testi")
    print(f"📍 Koordinatlar: Boylam={longitude}, Enlem={latitude}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # JSON request body oluştur
            request_data = {
                "method": "Manual",
                "longitude": longitude,
                "latitude": latitude
            }
            
            print(f"📤 Gönderilen JSON: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                "http://localhost:8000/analyze",
                json=request_data,
                timeout=30.0
            )
            
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Başarılı!")
                
                # Ham JSON response'u yazdır
                print("\n📋 Ham JSON Response:")
                print("=" * 50)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("=" * 50)
                
                # Özet bilgiler
                print(f"\n📊 Özet Bilgiler:")
                print(f"   🆔 Soil ID: {result.get('soil_id', 'N/A')}")
                
                classification = result.get('classification', {})
                print(f"   🌍 WRB4: {classification.get('wrb4_code', 'N/A')} - {classification.get('wrb4_description', 'N/A')}")
                print(f"   🌍 WRB2: {classification.get('wrb2_code', 'N/A')} - {classification.get('wrb2_description', 'N/A')}")
                print(f"   🌍 FAO90: {classification.get('fao90_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_auto_analysis():
    """Otomatik konum tespiti testi"""
    print(f"\n🌐 Otomatik Analiz Testi")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # JSON request body oluştur
            request_data = {
                "method": "Auto"
            }
            
            print(f"📤 Gönderilen JSON: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                "http://localhost:8000/analyze/auto",
                json=request_data,
                timeout=30.0
            )
            
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Başarılı!")
                
                # Ham JSON response'u yazdır
                print("\n📋 Ham JSON Response:")
                print("=" * 50)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("=" * 50)
                
                # Özet bilgiler
                print(f"\n📊 Özet Bilgiler:")
                coords = result.get('coordinates', {})
                print(f"   📍 Koordinatlar: Boylam={coords.get('longitude', 'N/A')}, Enlem={coords.get('latitude', 'N/A')}")
                print(f"   🆔 Soil ID: {result.get('soil_id', 'N/A')}")
                
                classification = result.get('classification', {})
                print(f"   🌍 WRB4: {classification.get('wrb4_code', 'N/A')} - {classification.get('wrb4_description', 'N/A')}")
                print(f"   🌍 WRB2: {classification.get('wrb2_code', 'N/A')} - {classification.get('wrb2_description', 'N/A')}")
                print(f"   🌍 FAO90: {classification.get('fao90_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_health_check():
    """Sağlık kontrolü testi"""
    print("🏥 Sağlık Kontrolü")
    print("-" * 30)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health", timeout=10.0)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API sağlıklı!")
                print(f"📊 Status: {result.get('status', 'N/A')}")
                print(f"🕒 Timestamp: {result.get('timestamp', 'N/A')}")
                return True
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Mesaj: {response.text}")
                return False
                
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
            return False
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")
            return False

async def main():
    """Ana test fonksiyonu"""
    print("🌍 Soil Analysis API Interactive Test Suite")
    print("=" * 60)
    
    # Sağlık kontrolü
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ API çalışmıyor! Lütfen API'yi başlatın.")
        return
    
    while True:
        choice = get_user_choice()
        
        if choice == "manual":
            longitude, latitude = get_manual_coordinates()
            if longitude is not None and latitude is not None:
                await test_manual_analysis(longitude, latitude)
            else:
                print("❌ Geçersiz koordinatlar!")
                
        elif choice == "auto":
            longitude, latitude = get_automatic_coordinates()
            if longitude is not None and latitude is not None:
                await test_auto_analysis()
            else:
                print("❌ Otomatik konum tespiti başarısız!")
                
        elif choice == "exit":
            print("\n👋 Çıkış yapılıyor...")
            break
        
        # Devam etmek isteyip istemediğini sor
        try:
            continue_choice = input("\nBaşka bir test yapmak ister misiniz? (e/h): ").strip().lower()
            if continue_choice not in ['e', 'evet', 'y', 'yes']:
                print("\n👋 Test tamamlandı!")
                break
        except KeyboardInterrupt:
            print("\n👋 Test tamamlandı!")
            break

if __name__ == "__main__":
    asyncio.run(main())