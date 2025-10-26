#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Machine Learning API Test Script
================================

Bu script, Machine Learning API'yi test etmek için örnek veriler ve test fonksiyonları içerir.
Mevcut test_api.py dosyasının güncellenmiş versiyonudur.

Author: ML API Test System
Version: 1.0.0
"""

import requests
import json
import time
from typing import Dict, Any, List
import pandas as pd

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """API bağlantısını test eder"""
    print("🔄 ML API bağlantısı test ediliyor...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/ml/")
        if response.status_code == 200:
            data = response.json()
            print("✅ ML API bağlantısı başarılı!")
            print(f"📊 Durum: {data.get('status', 'Bilinmiyor')}")
            print(f"📊 Model yüklü: {data.get('model_loaded', False)}")
            return True
        else:
            print(f"❌ ML API bağlantı hatası: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ML API'ye bağlanılamıyor. API çalışıyor mu?")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False

def test_health_endpoint():
    """Health endpoint'ini test eder"""
    print("\n🔄 Health endpoint test ediliyor...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/ml/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check başarılı!")
            print(f"📊 Model yüklü: {data.get('model_loaded', False)}")
            print(f"📊 Model adı: {data.get('model_name', 'Bilinmiyor')}")
            print(f"📊 Model skoru: {data.get('model_score', 'Bilinmiyor')}")
            return True
        else:
            print(f"❌ Health check hatası: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check hatası: {e}")
        return False

def test_model_info():
    """Model bilgilerini test eder"""
    print("\n🔄 Model bilgileri test ediliyor...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/ml/model-info")
        if response.status_code == 200:
            data = response.json()
            print("✅ Model bilgileri alındı!")
            print(f"📊 En iyi model: {data.get('best_model', 'Bilinmiyor')}")
            print(f"📊 F1-Macro skoru: {data.get('best_f1_macro', 'Bilinmiyor')}")
            print(f"📊 Özellik sayısı: {data.get('feature_count', 'Bilinmiyor')}")
            print(f"📊 Ürün sayısı: {data.get('crop_count', 'Bilinmiyor')}")
            print(f"📊 Eğitim tarihi: {data.get('training_date', 'Bilinmiyor')}")
            
            crop_names = data.get('crop_names', [])
            if crop_names:
                print(f"📊 İlk 10 ürün: {crop_names[:10]}")
            
            return data
        else:
            print(f"❌ Model bilgileri alınamadı: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Model bilgileri hatası: {e}")
        return None

def create_sample_data():
    """Örnek test verisi oluşturur"""
    print("\n🔄 Örnek test verisi oluşturuluyor...")
    
    # Çanakkale örneği (final4.csv'den)
    sample_data = {
        "method": "Manual",
        "wrb4_code": "TC",
        "physical_available_water_capacity": 0,
        "basic_organic_carbon": 1.93,
        "basic_c_n_ratio": 11.5,
        "texture_clay": 25.0,
        "texture_sand": 33.0,
        "texture_coarse_fragments": 5.0,
        "physical_reference_bulk_density": 1.78,
        "chemical_cation_exchange_capacity": 17.328,
        "chemical_clay_cec": 49.775,
        "chemical_total_exchangeable_bases": 25.549,
        "chemical_base_saturation": 84.274,
        "chemical_exchangeable_sodium_percentage": 2.042,
        "chemical_aluminum_saturation": 0.296,
        "salinity_electrical_conductivity": 0.911,
        "salinity_total_carbon_equivalent": 7.429,
        "salinity_gypsum_content": 0.752,
        "ortalama_en_yuksek_sicaklik_eylul": 26.7,
        "ortalama_en_yuksek_sicaklik_aralik": 11.5,
        "ortalama_en_dusuk_sicaklik_agustos": 21.2,
        "ortalama_guneslenme_suresi_agustos": 10.4,
        "ortalama_guneslenme_suresi_aralik": 2.8,
        "ortalama_yagisli_gun_sayisi_subat": 10.7,
        "ortalama_yagisli_gun_sayisi_mart": 10.47,
        "ortalama_yagisli_gun_sayisi_nisan": 8.83,
        "ortalama_yagisli_gun_sayisi_agustos": 1.2,
        "ortalama_yagisli_gun_sayisi_kasim": 8.77,
        "ortalama_yagisli_gun_sayisi_yillik": 87.1,
        "aylik_toplam_yagis_miktari_nisan": 49.0,
        "aylik_toplam_yagis_miktari_mayis": 32.1,
        "aylik_toplam_yagis_miktari_haziran": 27.3,
        "aylik_toplam_yagis_miktari_agustos": 6.8,
        "aylik_toplam_yagis_miktari_eylul": 24.2,
        "aylik_toplam_yagis_miktari_ekim": 67.5,
        "aylik_toplam_yagis_miktari_aralik": 100.4,
        "aylik_toplam_yagis_miktari_yillik": 620.3
    }
    
    print("✅ Örnek veri oluşturuldu!")
    print(f"📊 Toprak türü: {sample_data['wrb4_code']}")
    print(f"📊 Organik karbon: {sample_data['basic_organic_carbon']}")
    print(f"📊 Yıllık yağış: {sample_data['aylik_toplam_yagis_miktari_yillik']} mm")
    
    return sample_data

def test_predict_endpoint(sample_data: Dict[str, Any]):
    """Predict endpoint'ini test eder"""
    print("\n🔄 Predict endpoint test ediliyor...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ml/predict",
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Tahmin başarılı!")
            print(f"📊 Başarı: {data.get('success', False)}")
            print(f"📊 Zaman: {data.get('timestamp', 'Bilinmiyor')}")
            
            # İstatistikler
            stats = data.get('statistics', {})
            print(f"📊 Analiz edilen ürün: {stats.get('total_crops_analyzed', 'Bilinmiyor')}")
            print(f"📊 Önerilen ürün: {stats.get('recommended_crops', 'Bilinmiyor')}")
            print(f"📊 Öneri oranı: {stats.get('recommendation_rate', 'Bilinmiyor')}%")
            print(f"📊 Ortalama olasılık: {stats.get('average_probability', 'Bilinmiyor')}")
            print(f"📊 Yüksek güven ürün: {stats.get('high_confidence_crops', 'Bilinmiyor')}")
            
            # Tahminler
            predictions = data.get('predictions', [])
            if predictions:
                print("\n📊 ÜRÜN TAHMİNLERİ:")
                recommended_crops = [p for p in predictions if p.get('prediction', False)]
                
                print(f"✅ Önerilen ürünler ({len(recommended_crops)} adet):")
                for crop in recommended_crops[:10]:  # İlk 10'u göster
                    print(f"   • {crop.get('crop_name', 'Bilinmiyor')}: {crop.get('probability', 0):.3f} ({crop.get('confidence', 'Bilinmiyor')})")
                
                if len(recommended_crops) > 10:
                    print(f"   ... ve {len(recommended_crops) - 10} ürün daha")
            
            return data
        else:
            print(f"❌ Tahmin hatası: {response.status_code}")
            print(f"❌ Hata mesajı: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Tahmin hatası: {e}")
        return None

def test_predict_simple_endpoint(sample_data: Dict[str, Any]):
    """Predict-simple endpoint'ini test eder"""
    print("\n🔄 Predict-simple endpoint test ediliyor...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ml/predict-simple",
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Basit tahmin başarılı!")
            print(f"📊 Başarı: {data.get('success', False)}")
            print(f"📊 Mesaj: {data.get('message', 'Bilinmiyor')}")
            
            recommended_crops = data.get('recommended_crops', [])
            print(f"📊 Önerilen ürün sayısı: {len(recommended_crops)}")
            
            if recommended_crops:
                print("📊 ÖNERİLEN ÜRÜNLER:")
                for crop in recommended_crops[:10]:  # İlk 10'u göster
                    print(f"   • {crop.get('crop_name', 'Bilinmiyor')}: {crop.get('probability', 0):.3f} ({crop.get('confidence', 'Bilinmiyor')})")
                
                if len(recommended_crops) > 10:
                    print(f"   ... ve {len(recommended_crops) - 10} ürün daha")
            
            return data
        else:
            print(f"❌ Basit tahmin hatası: {response.status_code}")
            print(f"❌ Hata mesajı: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Basit tahmin hatası: {e}")
        return None

def test_analyze_auto_endpoint():
    """Analyze-auto endpoint'ini test eder"""
    print("\n🔄 Analyze-auto endpoint test ediliyor...")
    
    try:
        auto_data = {"method": "Auto"}
        
        response = requests.post(
            f"{API_BASE_URL}/ml/analyze-auto",
            json=auto_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Otomatik analiz başarılı!")
            print(f"📊 Başarı: {data.get('success', False)}")
            print(f"📊 Zaman: {data.get('timestamp', 'Bilinmiyor')}")
            
            # İstatistikler
            stats = data.get('statistics', {})
            print(f"📊 Analiz edilen ürün: {stats.get('total_crops_analyzed', 'Bilinmiyor')}")
            print(f"📊 Önerilen ürün: {stats.get('recommended_crops', 'Bilinmiyor')}")
            print(f"📊 Öneri oranı: {stats.get('recommendation_rate', 'Bilinmiyor')}%")
            
            # Tahminler
            predictions = data.get('predictions', [])
            if predictions:
                recommended_crops = [p for p in predictions if p.get('prediction', False)]
                print(f"📊 Önerilen ürün sayısı: {len(recommended_crops)}")
                
                if recommended_crops:
                    print("📊 ÖNERİLEN ÜRÜNLER:")
                    for crop in recommended_crops[:5]:  # İlk 5'ini göster
                        print(f"   • {crop.get('crop_name', 'Bilinmiyor')}: {crop.get('probability', 0):.3f} ({crop.get('confidence', 'Bilinmiyor')})")
            
            return data
        else:
            print(f"❌ Otomatik analiz hatası: {response.status_code}")
            print(f"❌ Hata mesajı: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Otomatik analiz hatası: {e}")
        return None

def test_performance():
    """Performans testi yapar"""
    print("\n🔄 Performans testi yapılıyor...")
    
    sample_data = create_sample_data()
    
    # 10 kez test et
    times = []
    for i in range(10):
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/ml/predict-simple",
                json=sample_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                end_time = time.time()
                response_time = end_time - start_time
                times.append(response_time)
                print(f"   Test {i+1}: {response_time:.3f} saniye")
            else:
                print(f"   Test {i+1}: HATA ({response.status_code})")
        except Exception as e:
            print(f"   Test {i+1}: HATA ({e})")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 PERFORMANS SONUÇLARI:")
        print(f"   Ortalama süre: {avg_time:.3f} saniye")
        print(f"   En hızlı: {min_time:.3f} saniye")
        print(f"   En yavaş: {max_time:.3f} saniye")
        print(f"   Başarılı test: {len(times)}/10")

def test_error_handling():
    """Hata yönetimi test eder"""
    print("\n🔄 Hata yönetimi test ediliyor...")
    
    # Geçersiz veri ile test
    invalid_data = {
        "method": "Manual",
        "wrb4_code": "INVALID",
        "basic_organic_carbon": "not_a_number",
        "texture_clay": -999  # Geçersiz değer
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ml/predict",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Geçersiz veri testi: {response.status_code}")
        if response.status_code != 200:
            print(f"✅ Hata yönetimi çalışıyor!")
            print(f"📊 Hata mesajı: {response.text[:100]}...")
        else:
            print(f"⚠️ Geçersiz veri kabul edildi")
    except Exception as e:
        print(f"❌ Hata yönetimi testi hatası: {e}")

def interactive_test():
    """İnteraktif test menüsü"""
    print("\n🌍 Machine Learning API Test - İnteraktif Mod")
    print("=" * 60)
    
    while True:
        print("\nTest seçenekleri:")
        print("1. Manuel koordinat ile tahmin")
        print("2. Otomatik konum tespiti ile tahmin")
        print("3. Model bilgilerini görüntüle")
        print("4. Performans testi")
        print("5. Hata yönetimi testi")
        print("6. Çıkış")
        
        choice = input("\nSeçiminiz (1-6): ").strip()
        
        if choice == "1":
            print("\n📍 Manuel Koordinat ile Tahmin")
            print("-" * 40)
            
            # Örnek veri oluştur
            sample_data = create_sample_data()
            
            # Tahmin yap
            result = test_predict_simple_endpoint(sample_data)
            
            if result:
                print("\n✅ Manuel tahmin tamamlandı!")
            else:
                print("\n❌ Manuel tahmin başarısız!")
        
        elif choice == "2":
            print("\n🌐 Otomatik Konum Tespiti ile Tahmin")
            print("-" * 40)
            print("Konumunuz otomatik olarak tespit ediliyor...")
            
            result = test_analyze_auto_endpoint()
            
            if result:
                print("\n✅ Otomatik analiz tamamlandı!")
            else:
                print("\n❌ Otomatik analiz başarısız!")
        
        elif choice == "3":
            print("\n📊 Model Bilgileri")
            print("-" * 40)
            test_model_info()
        
        elif choice == "4":
            print("\n⚡ Performans Testi")
            print("-" * 40)
            test_performance()
        
        elif choice == "5":
            print("\n🛡️ Hata Yönetimi Testi")
            print("-" * 40)
            test_error_handling()
        
        elif choice == "6":
            print("\n👋 Test tamamlandı!")
            break
        
        else:
            print("\n❌ Geçersiz seçim! Lütfen 1-6 arası bir sayı girin.")

def run_all_tests():
    """Tüm testleri çalıştırır"""
    print("🚀 MACHINE LEARNING API TEST BAŞLIYOR")
    print("=" * 60)
    
    # 1. Bağlantı testi
    if not test_api_connection():
        print("\n❌ API bağlantısı başarısız. Testler durduruluyor.")
        return
    
    # 2. Health check
    test_health_endpoint()
    
    # 3. Model bilgileri
    model_info = test_model_info()
    if not model_info:
        print("\n❌ Model bilgileri alınamadı. Testler durduruluyor.")
        return
    
    # 4. Örnek veri oluştur
    sample_data = create_sample_data()
    
    # 5. Tahmin testleri
    test_predict_endpoint(sample_data)
    test_predict_simple_endpoint(sample_data)
    
    # 6. Otomatik analiz testi
    test_analyze_auto_endpoint()
    
    # 7. Performans testi
    test_performance()
    
    # 8. Hata yönetimi testi
    test_error_handling()
    
    print("\n🎉 TÜM TESTLER TAMAMLANDI!")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # İnteraktif mod
        if test_api_connection():
            interactive_test()
        else:
            print("❌ API bağlantısı başarısız. İnteraktif mod başlatılamıyor.")
    else:
        # Otomatik test modu
        run_all_tests()
