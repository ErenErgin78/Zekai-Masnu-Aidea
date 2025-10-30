#!/usr/bin/env python3
"""
Weather API Interactive Test Script
=================================

Bu script, Weather API'sini interaktif olarak test eder.
Kullanıcıdan manuel/otomatik seçim alır ve hava durumu verilerini gösterir.
"""

import httpx
import asyncio
import json
import geocoder
from typing import Dict, Any
from datetime import date, datetime

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
        
        print(f"✅ Koordinatlar alındı: Boylam={longitude}, Enlem={latitude}")
        return longitude, latitude
        
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
            print(f"✅ Konum algılandı: Enlem={lat}, Boylam={lon}")
            print("(Not: Bu konum, IP adresinize dayalı bir tahmindir.)")
            return lon, lat
        else:
            print("❌ Konumunuz otomatik olarak algılanamadı.")
            return None, None
    except Exception as e:
        print(f"❌ Otomatik konum tespiti hatası: {e}")
        return None, None

def get_user_choice():
    """Kullanıcıdan test yöntemi seçimini alır"""
    print("\n🌤️ Weather API Test")
    print("=" * 40)
    print("Test yöntemini seçin:")
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

def get_weather_test_type():
    """Hava durumu test türünü seç"""
    print("\n🌦️ Hava Durumu Test Türü")
    print("-" * 30)
    print("Test etmek istediğiniz seçenek:")
    print("1. Günlük hava durumu (1-16 gün)")
    print("2. Saatlik hava durumu (1-16 gün)")
    print("3. Tarih aralığı ile günlük hava durumu")
    print("4. Geri dön")
    
    while True:
        try:
            choice = input("\nSeçiminiz (1-4): ").strip()
            
            if choice == "1":
                return "daily"
            elif choice == "2":
                return "hourly"
            elif choice == "3":
                return "daily_by_date"
            elif choice == "4":
                return "back"
            else:
                print("❌ Geçersiz seçim! Lütfen 1, 2, 3 veya 4 girin.")
        except KeyboardInterrupt:
            print("\n❌ İşlem iptal edildi")
            return "back"

def get_days_input():
    """Gün sayısı al"""
    try:
        days = int(input("Gün sayısı girin (1-16, varsayılan 1): ") or "1")
        if not (1 <= days <= 16):
            raise ValueError("Gün sayısı 1-16 arasında olmalıdır")
        return days
    except ValueError as e:
        print(f"❌ Geçersiz gün sayısı: {e}")
        return 1

def get_date_range():
    """Tarih aralığı al"""
    print("\n📅 Tarih Aralığı Girişi")
    print("-" * 30)
    
    try:
        start_date_str = input("Başlangıç tarihi (YYYY-MM-DD): ").strip()
        end_date_str = input("Bitiş tarihi (YYYY-MM-DD): ").strip()
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        if start_date > end_date:
            raise ValueError("Başlangıç tarihi bitiş tarihinden sonra olamaz")
        
        return start_date, end_date
        
    except ValueError as e:
        print(f"❌ Geçersiz tarih formatı: {e}")
        return None, None
    except KeyboardInterrupt:
        print("\n❌ İşlem iptal edildi")
        return None, None

async def test_daily_weather_manual(longitude, latitude, days=1):
    """Manuel koordinat ile günlük hava durumu testi"""
    print(f"\n🌤️ Günlük Hava Durumu Testi (Manuel)")
    print(f"📍 Koordinatlar: Boylam={longitude}, Enlem={latitude}")
    print(f"📅 Gün sayısı: {days}")
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
                f"http://localhost:8000/weather/dailyweather/manual?days={days}",
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
                if isinstance(result, list) and result:
                    first_day = result[0]
                    print(f"   📅 İlk Gün: {first_day.get('day', 'N/A')}")
                    print(f"   🌡️ Ortalama Sıcaklık: {first_day.get('temperature_2m_mean', 'N/A')}°C")
                    print(f"   🌧️ Yağış Toplamı: {first_day.get('precipitation_sum', 'N/A')}mm")
                    print(f"   🌤️ Hava Durumu: {first_day.get('weather_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_daily_weather_auto(days=1):
    """Otomatik konum ile günlük hava durumu testi"""
    print(f"\n🌤️ Günlük Hava Durumu Testi (Otomatik)")
    print(f"📅 Gün sayısı: {days}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # JSON request body oluştur
            request_data = {
                "method": "Auto"
            }
            
            print(f"📤 Gönderilen JSON: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                f"http://localhost:8000/weather/dailyweather/auto?days={days}",
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
                if isinstance(result, list) and result:
                    first_day = result[0]
                    print(f"   📅 İlk Gün: {first_day.get('day', 'N/A')}")
                    print(f"   🌡️ Ortalama Sıcaklık: {first_day.get('temperature_2m_mean', 'N/A')}°C")
                    print(f"   🌧️ Yağış Toplamı: {first_day.get('precipitation_sum', 'N/A')}mm")
                    print(f"   🌤️ Hava Durumu: {first_day.get('weather_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_hourly_weather_manual(longitude, latitude, days=1):
    """Manuel koordinat ile saatlik hava durumu testi"""
    print(f"\n⏰ Saatlik Hava Durumu Testi (Manuel)")
    print(f"📍 Koordinatlar: Boylam={longitude}, Enlem={latitude}")
    print(f"📅 Gün sayısı: {days}")
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
                f"http://localhost:8000/weather/hourlyweather/manual?days={days}",
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
                if isinstance(result, list) and result:
                    first_hour = result[0]
                    print(f"   ⏰ İlk Saat: {first_hour.get('time', 'N/A')}")
                    print(f"   🌡️ Sıcaklık: {first_hour.get('temperature_2m', 'N/A')}°C")
                    print(f"   💧 Nem: {first_hour.get('relative_humidity_2m', 'N/A')}%")
                    print(f"   🌤️ Hava Durumu: {first_hour.get('weather_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_hourly_weather_auto(days=1):
    """Otomatik konum ile saatlik hava durumu testi"""
    print(f"\n⏰ Saatlik Hava Durumu Testi (Otomatik)")
    print(f"📅 Gün sayısı: {days}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # JSON request body oluştur
            request_data = {
                "method": "Auto"
            }
            
            print(f"📤 Gönderilen JSON: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                f"http://localhost:8000/weather/hourlyweather/auto?days={days}",
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
                if isinstance(result, list) and result:
                    first_hour = result[0]
                    print(f"   ⏰ İlk Saat: {first_hour.get('time', 'N/A')}")
                    print(f"   🌡️ Sıcaklık: {first_hour.get('temperature_2m', 'N/A')}°C")
                    print(f"   💧 Nem: {first_hour.get('relative_humidity_2m', 'N/A')}%")
                    print(f"   🌤️ Hava Durumu: {first_hour.get('weather_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_daily_weather_by_date_manual(longitude, latitude, start_date, end_date):
    """Manuel koordinat ile tarih aralığı günlük hava durumu testi"""
    print(f"\n📅 Tarih Aralığı Günlük Hava Durumu Testi (Manuel)")
    print(f"📍 Koordinatlar: Boylam={longitude}, Enlem={latitude}")
    print(f"📅 Tarih Aralığı: {start_date} - {end_date}")
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
                f"http://localhost:8000/weather/dailyweather/bydate/manual/{start_date}/{end_date}",
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
                if isinstance(result, list) and result:
                    first_day = result[0]
                    print(f"   📅 İlk Gün: {first_day.get('day', 'N/A')}")
                    print(f"   🌡️ Ortalama Sıcaklık: {first_day.get('temperature_2m_mean', 'N/A')}°C")
                    print(f"   🌧️ Yağış Toplamı: {first_day.get('precipitation_sum', 'N/A')}mm")
                    print(f"   🌤️ Hava Durumu: {first_day.get('weather_code', 'N/A')}")
                
            else:
                print(f"❌ Hata: {response.status_code}")
                print(f"📝 Hata Mesajı: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Zaman aşımı!")
        except httpx.ConnectError:
            print("🔌 Bağlantı hatası! API çalışıyor mu?")
        except Exception as e:
            print(f"💥 Beklenmeyen hata: {e}")

async def test_daily_weather_by_date_auto(start_date, end_date):
    """Otomatik konum ile tarih aralığı günlük hava durumu testi"""
    print(f"\n📅 Tarih Aralığı Günlük Hava Durumu Testi (Otomatik)")
    print(f"📅 Tarih Aralığı: {start_date} - {end_date}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # JSON request body oluştur
            request_data = {
                "method": "Auto"
            }
            
            print(f"📤 Gönderilen JSON: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                f"http://localhost:8000/weather/dailyweather/bydate/auto/{start_date}/{end_date}",
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
                if isinstance(result, list) and result:
                    first_day = result[0]
                    print(f"   📅 İlk Gün: {first_day.get('day', 'N/A')}")
                    print(f"   🌡️ Ortalama Sıcaklık: {first_day.get('temperature_2m_mean', 'N/A')}°C")
                    print(f"   🌧️ Yağış Toplamı: {first_day.get('precipitation_sum', 'N/A')}mm")
                    print(f"   🌤️ Hava Durumu: {first_day.get('weather_code', 'N/A')}")
                
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
                print("✅ Weather API sağlıklı!")
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
    print("🌤️ Weather API Interactive Test Suite")
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
                weather_type = get_weather_test_type()
                
                if weather_type == "daily":
                    days = get_days_input()
                    await test_daily_weather_manual(longitude, latitude, days)
                elif weather_type == "hourly":
                    days = get_days_input()
                    await test_hourly_weather_manual(longitude, latitude, days)
                elif weather_type == "daily_by_date":
                    start_date, end_date = get_date_range()
                    if start_date and end_date:
                        await test_daily_weather_by_date_manual(longitude, latitude, start_date, end_date)
                elif weather_type == "back":
                    continue
            else:
                print("❌ Geçersiz koordinatlar!")
                
        elif choice == "auto":
            longitude, latitude = get_automatic_coordinates()
            if longitude is not None and latitude is not None:
                weather_type = get_weather_test_type()
                
                if weather_type == "daily":
                    days = get_days_input()
                    await test_daily_weather_auto(days)
                elif weather_type == "hourly":
                    days = get_days_input()
                    await test_hourly_weather_auto(days)
                elif weather_type == "daily_by_date":
                    start_date, end_date = get_date_range()
                    if start_date and end_date:
                        await test_daily_weather_by_date_auto(start_date, end_date)
                elif weather_type == "back":
                    continue
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
