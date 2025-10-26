# 🤖 Machine Learning API - FastAPI Implementation

Bu API, makine öğrenmesi modeli kullanarak tarım ürünü önerisi yapan bir servistir. Multi-label classification yaklaşımı ile çoklu ürün tahmini yapar ve mevcut Soil API ile Weather API'leri entegre ederek otomatik analiz sağlar.

## 🌟 Özellikler

- **Manuel Veri Girişi**: Toprak ve iklim verilerini manuel olarak girerek tahmin yapma
- **Otomatik Analiz**: IP tabanlı konum tespiti + toprak analizi + hava durumu + ürün önerisi
- **Multi-label Classification**: Çoklu ürün tahmini (bir konumda birden fazla ürün önerisi)
- **Detaylı Tahmin Sonuçları**: Olasılık skorları ve güven seviyeleri
- **JSON Formatında Sonuçlar**: RESTful API yapısı
- **Güvenlik Korumaları**: Input validation ve SQL injection koruması
- **Kapsamlı Hata Yönetimi**: Detaylı error handling ve logging

## 🏗️ Sistem Mimarisi

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Soil API      │    │   Weather API   │    │   ML API        │
│                 │    │                 │    │                 │
│ • HWSD2 DB      │    │ • Open-Meteo    │    │ • Multi-label   │
│ • Koordinat     │    │ • Günlük/Saatlik│    │ • 8 Algoritma   │
│ • Toprak Analizi│    │ • Otomatik Konum│    │ • F1-Macro      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Main API      │
                    │                 │
                    │ • Entegrasyon   │
                    │ • Otomatik Analiz│
                    │ • Tek Endpoint  │
                    └─────────────────┘
```

## 📁 Dosya Yapısı

```
Backend/API/MachineLearning/
├── ml_api.py              # Ana ML API dosyası
├── test_ml_api.py         # Test scripti
├── Model/
│   └── model.pkl          # Eğitilmiş ML modeli
└── README.md              # Bu dokümantasyon
```

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimler
```bash
pip install fastapi uvicorn pandas numpy scikit-learn joblib
pip install requests geocoder
```

### 2. Model Dosyası
`Model/model.pkl` dosyasının mevcut olduğundan emin olun. Bu dosya şu yapıda olmalıdır:
```python
{
    'model': trained_model,      # Eğitilmiş model
    'scaler': fitted_scaler,     # Özellik ölçekleyici
    'metadata': {                # Model bilgileri
        'best_model': 'RandomForest',
        'best_f1_macro': 0.9487,
        'feature_count': 36,
        'crop_count': 37,
        'training_date': '2024-01-01',
        'crop_names': ['Buğday', 'Arpa', ...]
    }
}
```

### 3. API'yi Başlatma
```bash
cd Backend/API/MachineLearning
python ml_api.py
```

### 4. Ana API ile Entegrasyon
ML API'yi ana API'ye entegre etmek için `main.py` dosyasına ekleyin:
```python
from MachineLearning.ml_api import router as ml_router
app.include_router(ml_router)
```

## 📊 API Endpoint'leri

### Ana Endpoint'ler

#### `GET /ml/`
API bilgileri ve durum kontrolü
```json
{
    "message": "Machine Learning API",
    "version": "1.0.0",
    "status": "running",
    "model_loaded": true,
    "docs": "/docs"
}
```

#### `GET /ml/health`
Sistem sağlık kontrolü
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00",
    "service": "Machine Learning API",
    "model_loaded": true,
    "model_name": "RandomForest",
    "model_score": 0.9487
}
```

#### `GET /ml/model-info`
Model bilgileri ve performans metrikleri
```json
{
    "success": true,
    "message": "Model information retrieved successfully",
    "timestamp": "2024-01-01T12:00:00",
    "best_model": "RandomForest",
    "best_f1_macro": 0.9487,
    "feature_count": 36,
    "crop_count": 37,
    "training_date": "2024-01-01",
    "crop_names": ["Buğday", "Arpa", "Domates", ...]
}
```

### Tahmin Endpoint'leri

#### `POST /ml/predict` ⭐ **DETAYLI TAHMİN**
Manuel veri ile detaylı ürün tahmini
```json
{
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
```

**Yanıt:**
```json
{
    "success": true,
    "message": "Crop prediction completed successfully",
    "timestamp": "2024-01-01T12:00:00",
    "statistics": {
        "total_crops_analyzed": 37,
        "recommended_crops": 15,
        "recommendation_rate": 40.54,
        "average_probability": 0.823,
        "high_confidence_crops": 8
    },
    "predictions": [
        {
            "crop_name": "Buğday",
            "prediction": true,
            "probability": 0.9234,
            "confidence": "Yüksek"
        },
        {
            "crop_name": "Arpa",
            "prediction": true,
            "probability": 0.8765,
            "confidence": "Yüksek"
        },
        {
            "crop_name": "Domates",
            "prediction": false,
            "probability": 0.2341,
            "confidence": "Düşük"
        }
    ]
}
```

#### `POST /ml/predict-simple` ⭐ **BASİT TAHMİN**
Sadece önerilen ürünleri döndürür
```json
{
    "method": "Manual",
    "wrb4_code": "TC",
    // ... diğer özellikler
}
```

**Yanıt:**
```json
{
    "success": true,
    "message": "Found 15 recommended crops",
    "timestamp": "2024-01-01T12:00:00",
    "recommended_crops": [
        {
            "crop_name": "Buğday",
            "prediction": true,
            "probability": 0.9234,
            "confidence": "Yüksek"
        },
        {
            "crop_name": "Arpa",
            "prediction": true,
            "probability": 0.8765,
            "confidence": "Yüksek"
        }
    ]
}
```

#### `POST /ml/analyze-auto` ⭐ **OTOMATİK ANALİZ**
IP tabanlı konum tespiti + toprak analizi + hava durumu + ürün önerisi
```json
{
    "method": "Auto"
}
```

**Yanıt:**
```json
{
    "success": true,
    "message": "Crop prediction completed successfully",
    "timestamp": "2024-01-01T12:00:00",
    "statistics": {
        "total_crops_analyzed": 37,
        "recommended_crops": 12,
        "recommendation_rate": 32.43,
        "average_probability": 0.789,
        "high_confidence_crops": 6
    },
    "predictions": [
        {
            "crop_name": "Buğday",
            "prediction": true,
            "probability": 0.9123,
            "confidence": "Yüksek"
        }
    ]
}
```

## 🔧 Teknik Detaylar

### Makine Öğrenmesi Modeli
- **Algoritma**: RandomForest (En iyi performans)
- **F1-Macro Skoru**: 0.9487
- **Yaklaşım**: Multi-label Classification (Binary Relevance)
- **Özellik Sayısı**: 36 (toprak + iklim verileri)
- **Ürün Sayısı**: 37 farklı tarım ürünü
- **Cross-validation**: Stratified K-Fold

### Özellik Mühendisliği
Model şu özellikleri kullanır:

#### Toprak Özellikleri (16 adet)
- `wrb4_code`: Toprak türü kodu
- `physical_available_water_capacity`: Su kapasitesi
- `basic_organic_carbon`: Organik karbon (%)
- `basic_c_n_ratio`: C/N oranı
- `texture_clay`: Kil oranı (%)
- `texture_sand`: Kum oranı (%)
- `texture_coarse_fragments`: Kaba parçacık oranı (%)
- `physical_reference_bulk_density`: Referans hacim yoğunluğu
- `chemical_cation_exchange_capacity`: Katyon değişim kapasitesi
- `chemical_clay_cec`: Kil CEC
- `chemical_total_exchangeable_bases`: Toplam değişebilir bazlar
- `chemical_base_saturation`: Baz doygunluğu (%)
- `chemical_exchangeable_sodium_percentage`: Değişebilir sodyum yüzdesi (%)
- `chemical_aluminum_saturation`: Alüminyum doygunluğu (%)
- `salinity_electrical_conductivity`: Elektriksel iletkenlik
- `salinity_total_carbon_equivalent`: Toplam karbon eşdeğeri
- `salinity_gypsum_content`: Jips içeriği

#### İklim Özellikleri (20 adet)
- `ortalama_en_yuksek_sicaklik_eylul`: Eylül ortalama en yüksek sıcaklık
- `ortalama_en_yuksek_sicaklik_aralik`: Aralık ortalama en yüksek sıcaklık
- `ortalama_en_dusuk_sicaklik_agustos`: Ağustos ortalama en düşük sıcaklık
- `ortalama_guneslenme_suresi_agustos`: Ağustos güneşlenme süresi
- `ortalama_guneslenme_suresi_aralik`: Aralık güneşlenme süresi
- `ortalama_yagisli_gun_sayisi_subat`: Şubat yağışlı gün sayısı
- `ortalama_yagisli_gun_sayisi_mart`: Mart yağışlı gün sayısı
- `ortalama_yagisli_gun_sayisi_nisan`: Nisan yağışlı gün sayısı
- `ortalama_yagisli_gun_sayisi_agustos`: Ağustos yağışlı gün sayısı
- `ortalama_yagisli_gun_sayisi_kasim`: Kasım yağışlı gün sayısı
- `ortalama_yagisli_gun_sayisi_yillik`: Yıllık yağışlı gün sayısı
- `aylik_toplam_yagis_miktari_nisan`: Nisan aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_mayis`: Mayıs aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_haziran`: Haziran aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_agustos`: Ağustos aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_eylul`: Eylül aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_ekim`: Ekim aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_aralik`: Aralık aylık toplam yağış miktarı
- `aylik_toplam_yagis_miktari_yillik`: Yıllık toplam yağış miktarı

### Güven Seviyeleri
- **Yüksek**: Olasılık ≥ 0.8
- **Orta**: Olasılık ≥ 0.6
- **Düşük**: Olasılık ≥ 0.4
- **Çok Düşük**: Olasılık < 0.4

## 🧪 Test Sistemi

### Test Scripti Kullanımı
```bash
# Otomatik test
python test_ml_api.py

# İnteraktif test
python test_ml_api.py --interactive
```

### Test Edilen Özellikler
- ✅ API bağlantısı
- ✅ Health check
- ✅ Model bilgileri
- ✅ Manuel tahmin
- ✅ Basit tahmin
- ✅ **Otomatik analiz** (Ana özellik)
- ✅ Performans testi
- ✅ Hata yönetimi

### Test Sonuçları Örneği
```
🚀 MACHINE LEARNING API TEST BAŞLIYOR
============================================================
🔄 ML API bağlantısı test ediliyor...
✅ ML API bağlantısı başarılı!
📊 Durum: running
📊 Model yüklü: True

🔄 Health endpoint test ediliyor...
✅ Health check başarılı!
📊 Model yüklü: True
📊 Model adı: RandomForest
📊 Model skoru: 0.9487

🔄 Model bilgileri test ediliyor...
✅ Model bilgileri alındı!
📊 En iyi model: RandomForest
📊 F1-Macro skoru: 0.9487
📊 Özellik sayısı: 36
📊 Ürün sayısı: 37
📊 Eğitim tarihi: 2024-01-01
📊 İlk 10 ürün: ['Buğday', 'Arpa', 'Domates', 'Zeytin', 'Pamuk', 'Mısır', 'Ayçiçeği', 'Şeker Pancarı', 'Patates', 'Soğan']

🔄 Örnek test verisi oluşturuluyor...
✅ Örnek veri oluşturuldu!
📊 Toprak türü: TC
📊 Organik karbon: 1.93
📊 Yıllık yağış: 620.3 mm

🔄 Predict endpoint test ediliyor...
✅ Tahmin başarılı!
📊 Başarı: True
📊 Zaman: 2024-01-01T12:00:00
📊 Analiz edilen ürün: 37
📊 Önerilen ürün: 15
📊 Öneri oranı: 40.54%
📊 Ortalama olasılık: 0.823
📊 Yüksek güven ürün: 8

📊 ÜRÜN TAHMİNLERİ:
✅ Önerilen ürünler (15 adet):
   • Buğday: 0.923 (Yüksek)
   • Arpa: 0.876 (Yüksek)
   • Domates: 0.834 (Yüksek)
   • Zeytin: 0.789 (Orta)
   • Pamuk: 0.756 (Orta)
   • Mısır: 0.723 (Orta)
   • Ayçiçeği: 0.689 (Orta)
   • Şeker Pancarı: 0.656 (Orta)
   • Patates: 0.623 (Orta)
   • Soğan: 0.590 (Orta)
   ... ve 5 ürün daha

🎉 TÜM TESTLER TAMAMLANDI!
============================================================
```

## 🌍 Kullanım Senaryoları

### 1. Çiftçi Uygulaması
```javascript
// Frontend'den otomatik analiz
const response = await fetch('/ml/analyze-auto', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ method: 'Auto' })
});

const data = await response.json();
console.log(`Önerilen ürünler: ${data.statistics.recommended_crops}`);
```

### 2. Tarım Danışmanlığı
- Konum bazlı toprak analizi
- İklim verisi ile ürün önerisi
- Risk değerlendirmesi
- Çoklu ürün kombinasyonları

### 3. Araştırma ve Geliştirme
- Toprak-ürün ilişkisi analizi
- İklim değişikliği etkisi
- Veri madenciliği
- Model performans analizi

## 🔮 Gelecek Özellikler

- [ ] Geçmiş veri analizi
- [ ] Tahmin güvenilirlik skorları
- [ ] Ürün rotasyon önerileri
- [ ] Verim tahmini
- [ ] Hastalık risk analizi
- [ ] Su ihtiyacı hesaplama
- [ ] Ekonomik analiz
- [ ] Sürdürülebilirlik skorları

## 📞 Destek

API dokümantasyonu: `http://localhost:8000/docs`
Swagger UI: `http://localhost:8000/redoc`

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.