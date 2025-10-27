# -*- coding: utf-8 -*-
"""
ML API Test Dosyası
==================

Bu dosya ML API'sinin çalışıp çalışmadığını test eder.
"""

import requests
import json
import logging

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_api():
    """ML API'sini test et"""
    
    # API URL'i
    base_url = "http://localhost:8000"
    ml_url = f"{base_url}/ml"
    
    print("=" * 50)
    print("ML API Test Başlatılıyor...")
    print("=" * 50)
    
    # 1. Health check testi
    print("\n1. Health Check Testi:")
    try:
        response = requests.get(f"{ml_url}/health")
        if response.status_code == 200:
            print("✅ Health check başarılı")
            print(f"   Yanıt: {response.json()}")
        else:
            print(f"❌ Health check başarısız: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check hatası: {str(e)}")
        return False
    
    # 2. Otomatik analiz testi
    print("\n2. Otomatik Analiz Testi:")
    try:
        payload = {"method": "Auto"}
        response = requests.post(f"{ml_url}/analyze", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Otomatik analiz başarılı")
            print(f"   Koordinatlar: {result.get('coordinates')}")
            print(f"   Öneri sayısı: {len(result.get('recommendations', []))}")
            
            # Model durumunu göster
            model_info = result.get('model_info', {})
            if model_info.get('fallback_mode'):
                print("   ⚠️  Fallback mode aktif - Model dosyası bozuk")
                print(f"   Model durumu: {model_info.get('model_status')}")
            else:
                print("   ✅ Model aktif")
                print(f"   Model tipi: {model_info.get('model_type')}")
                print(f"   Scaler tipi: {model_info.get('scaler_type')}")
                if model_info.get('metadata'):
                    print(f"   Metadata: {model_info.get('metadata')}")
            
            # İlk 3 öneriyi göster
            recommendations = result.get('recommendations', [])
            if recommendations:
                print("   En iyi öneriler:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"     {i}. {rec['plant_name']} - Güven: %{rec['confidence_score']}")
        else:
            print(f"❌ Otomatik analiz başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Otomatik analiz hatası: {str(e)}")
        return False
    
    # 3. Manuel analiz testi
    print("\n3. Manuel Analiz Testi:")
    try:
        payload = {
            "method": "Manual",
            "coordinates": {
                "longitude": 35.0,
                "latitude": 40.0
            }
        }
        response = requests.post(f"{ml_url}/analyze", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Manuel analiz başarılı")
            print(f"   Koordinatlar: {result.get('coordinates')}")
            print(f"   Öneri sayısı: {len(result.get('recommendations', []))}")
            
            # Model durumunu göster
            model_info = result.get('model_info', {})
            if model_info.get('fallback_mode'):
                print("   ⚠️  Fallback mode aktif - Model dosyası bozuk")
                print(f"   Model durumu: {model_info.get('model_status')}")
            else:
                print("   ✅ Model aktif")
                print(f"   Model tipi: {model_info.get('model_type')}")
                print(f"   Scaler tipi: {model_info.get('scaler_type')}")
                if model_info.get('metadata'):
                    print(f"   Metadata: {model_info.get('metadata')}")
            
            # İlk 3 öneriyi göster
            recommendations = result.get('recommendations', [])
            if recommendations:
                print("   En iyi öneriler:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"     {i}. {rec['plant_name']} - Güven: %{rec['confidence_score']}")
        else:
            print(f"❌ Manuel analiz başarısız: {response.status_code}")
            print(f"   Hata: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Manuel analiz hatası: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Tüm testler başarılı!")
    print("=" * 50)
    return True

def test_soil_api():
    """SoilType API'sinin çalışıp çalışmadığını test et"""
    
    print("\n" + "=" * 50)
    print("SoilType API Testi...")
    print("=" * 50)
    
    try:
        # SoilType API health check
        response = requests.get("http://localhost:8000/soiltype/health")
        if response.status_code == 200:
            print("✅ SoilType API çalışıyor")
        else:
            print(f"❌ SoilType API sorunu: {response.status_code}")
            return False
            
        # Otomatik analiz testi
        payload = {"method": "Auto"}
        response = requests.post("http://localhost:8000/soiltype/analyze/auto", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SoilType otomatik analiz başarılı")
            print(f"   Koordinatlar: {result.get('coordinates')}")
            print(f"   Toprak ID: {result.get('soil_id')}")
        else:
            print(f"❌ SoilType analiz başarısız: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ SoilType API hatası: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("ML API Test Suite")
    print("Bu test ML API'sinin ve bağımlılıklarının çalışıp çalışmadığını kontrol eder.")
    print("\nNot: Test öncesi API'nin çalıştığından emin olun:")
    print("   python -m uvicorn Backend.API.main:app --reload")
    
    # SoilType API testi
    soil_ok = test_soil_api()
    
    if soil_ok:
        # ML API testi
        ml_ok = test_ml_api()
        
        if ml_ok:
            print("\n🎉 Tüm sistemler çalışıyor!")
        else:
            print("\n❌ ML API'de sorun var")
    else:
        print("\n❌ SoilType API'de sorun var, ML API test edilemiyor")
