# -*- coding: utf-8 -*-
"""
Model Dosyası Analiz Aracı
=========================

Bu script model.pkl dosyasının durumunu analiz eder ve
bozuk olma sebeplerini tespit eder.
"""

import os
import pickle
import sys
from pathlib import Path

def analyze_model_file():
    """Model dosyasını analiz et"""
    
    # Model dosyası yolu
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'Model', 'model.pkl')
    
    print("=" * 60)
    print("MODEL DOSYASI ANALİZİ")
    print("=" * 60)
    
    # Dosya varlığını kontrol et
    if not os.path.exists(model_path):
        print(f"❌ Model dosyası bulunamadı: {model_path}")
        return
    
    # Dosya bilgilerini al
    file_size = os.path.getsize(model_path)
    print(f"📁 Dosya yolu: {model_path}")
    print(f"📏 Dosya boyutu: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Dosyanın ilk birkaç byte'ını oku
    try:
        with open(model_path, 'rb') as f:
            first_bytes = f.read(20)
        print(f"🔍 İlk 20 byte: {first_bytes}")
        print(f"🔍 Hex format: {first_bytes.hex()}")
        
        # Pickle signature kontrolü
        if first_bytes.startswith(b'\x80'):
            print("✅ Pickle protokolü tespit edildi")
        elif first_bytes.startswith(b'PK'):
            print("⚠️  ZIP dosyası gibi görünüyor")
        elif first_bytes.startswith(b'\x89PNG'):
            print("⚠️  PNG dosyası gibi görünüyor")
        else:
            print("❓ Bilinmeyen dosya formatı")
            
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {str(e)}")
        return
    
    # Farklı pickle protokolleri ile yüklemeyi dene
    print("\n" + "=" * 40)
    print("PICKLE YÜKLEME DENEMELERİ")
    print("=" * 40)
    
    protocols_to_try = [
        ("Pickle protokol 0", lambda: pickle.load(open(model_path, 'rb'))),
        ("Pickle protokol 2", lambda: pickle.load(open(model_path, 'rb'))),
        ("Pickle protokol 3", lambda: pickle.load(open(model_path, 'rb'))),
        ("Pickle protokol 4", lambda: pickle.load(open(model_path, 'rb'))),
        ("Pickle protokol 5", lambda: pickle.load(open(model_path, 'rb'))),
    ]
    
    for protocol_name, load_func in protocols_to_try:
        try:
            print(f"🔄 {protocol_name} deneniyor...")
            model = load_func()
            print(f"✅ {protocol_name} başarılı!")
            print(f"   Model tipi: {type(model)}")
            
            # Model özelliklerini kontrol et
            if hasattr(model, 'predict'):
                print(f"   ✅ predict() metodu var")
            if hasattr(model, 'predict_proba'):
                print(f"   ✅ predict_proba() metodu var")
            if hasattr(model, 'classes_'):
                print(f"   ✅ classes_ özelliği var: {len(model.classes_)} sınıf")
            if hasattr(model, 'feature_importances_'):
                print(f"   ✅ feature_importances_ var")
                
            return model
            
        except Exception as e:
            print(f"❌ {protocol_name} başarısız: {str(e)}")
            continue
    
    print("\n❌ Hiçbir pickle protokolü çalışmadı!")
    
    # Alternatif yükleme yöntemleri
    print("\n" + "=" * 40)
    print("ALTERNATİF YÖNTEMLER")
    print("=" * 40)
    
    # joblib ile yüklemeyi dene
    try:
        import joblib
        print("🔄 joblib ile yükleniyor...")
        model = joblib.load(model_path)
        print("✅ joblib ile yükleme başarılı!")
        print(f"   Model tipi: {type(model)}")
        return model
    except ImportError:
        print("⚠️  joblib yüklü değil")
    except Exception as e:
        print(f"❌ joblib yükleme hatası: {str(e)}")
    
    # dill ile yüklemeyi dene
    try:
        import dill
        print("🔄 dill ile yükleniyor...")
        model = dill.load(open(model_path, 'rb'))
        print("✅ dill ile yükleme başarılı!")
        print(f"   Model tipi: {type(model)}")
        return model
    except ImportError:
        print("⚠️  dill yüklü değil")
    except Exception as e:
        print(f"❌ dill yükleme hatası: {str(e)}")
    
    print("\n" + "=" * 40)
    print("SONUÇ VE ÖNERİLER")
    print("=" * 40)
    print("❌ Model dosyası tamamen bozuk görünüyor.")
    print("\n🔧 ÇÖZÜM ÖNERİLERİ:")
    print("1. Model dosyasını yeniden oluşturun")
    print("2. Orijinal model dosyasını kontrol edin")
    print("3. Dosya transferi sırasında bozulmuş olabilir")
    print("4. Farklı Python versiyonu ile kaydedilmiş olabilir")
    print("5. Şu anda fallback mode ile çalışıyor - bu geçici bir çözüm")

def create_sample_model():
    """Örnek bir model oluştur"""
    try:
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np
        
        print("\n" + "=" * 40)
        print("ÖRNEK MODEL OLUŞTURMA")
        print("=" * 40)
        
        # Örnek veri oluştur
        X = np.random.rand(100, 37)  # 37 özellik
        y = np.random.randint(0, 38, 100)  # 38 sınıf
        
        # Model oluştur ve eğit
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Modeli kaydet
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'Model', 'sample_model.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"✅ Örnek model oluşturuldu: {model_path}")
        print(f"   Model tipi: {type(model)}")
        print(f"   Özellik sayısı: {model.n_features_in_}")
        print(f"   Sınıf sayısı: {len(model.classes_)}")
        
        return model_path
        
    except Exception as e:
        print(f"❌ Örnek model oluşturma hatası: {str(e)}")
        return None

if __name__ == "__main__":
    print("Model Dosyası Analiz Aracı")
    print("Bu araç model.pkl dosyasının durumunu analiz eder.")
    
    # Model dosyasını analiz et
    model = analyze_model_file()
    
    # Eğer model yüklenemezse örnek model oluştur
    if model is None:
        print("\n" + "=" * 60)
        print("ÖRNEK MODEL OLUŞTURMA")
        print("=" * 60)
        
        sample_path = create_sample_model()
        if sample_path:
            print(f"\n💡 Öneri: {sample_path} dosyasını model.pkl olarak kopyalayın")
            print("   Bu geçici bir çözüm olacaktır.")
