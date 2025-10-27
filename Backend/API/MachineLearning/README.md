# Machine Learning API

Bu API, koordinat bilgilerine göre toprak analizi yaparak makine öğrenmesi modeli ile bitki önerileri sunar.

## Özellikler

- **Toprak Analizi**: SoilType API'sinden toprak verilerini alır
- **İklim Verileri**: Koordinatlara göre iklim verilerini eşleştirir
- **Bitki Önerileri**: ML modeli ile en uygun bitkileri önerir
- **Dinamik Yollar**: Farklı sistemlerde çalışabilir
- **Hata Yönetimi**: Kapsamlı hata yakalama ve loglama
- **RESTful API**: FastAPI ile modern API tasarımı

## Kurulum

### Gereksinimler

```bash
pip install -r requirements.txt
```

### Bağımlılıklar

- `fastapi`: Web API framework
- `pandas`: Veri işleme
- `numpy`: Sayısal hesaplamalar
- `scikit-learn`: Makine öğrenmesi
- `requests`: HTTP istekleri
- `pydantic`: Veri validasyonu

## Kullanım

### API Başlatma

```bash
# Ana API'yi başlat (ML API dahil)
python -m uvicorn Backend.API.main:app --reload

# Sadece ML API'yi başlat
python Backend/API/MachineLearning/ml_api.py
```

### Endpoint'ler

#### 1. Health Check
```http
GET /ml/health
```

#### 2. Otomatik Analiz
```http
POST /ml/analyze
Content-Type: application/json

{
    "method": "Auto"
}
```

#### 3. Manuel Analiz
```http
POST /ml/analyze
Content-Type: application/json

{
    "method": "Manual",
    "coordinates": {
        "longitude": 35.0,
        "latitude": 40.0
    }
}
```

### Yanıt Formatı

```json
{
    "success": true,
    "message": "ML analysis completed successfully",
    "timestamp": "2024-01-01T12:00:00",
    "coordinates": {
        "longitude": 35.0,
        "latitude": 40.0
    },
    "soil_data": {
        "wrb4_code": 21,
        "physical_available_water_capacity": 0.0,
        "basic_organic_carbon": 1.93,
        // ... diğer toprak özellikleri
    },
    "climate_data": {
        "Ortalama En Yüksek Sıcaklık (°C)_Eylül": 26.7,
        "Ortalama En Yüksek Sıcaklık (°C)_Aralık": 11.5,
        // ... diğer iklim verileri
    },
    "recommendations": [
        {
            "plant_name": "Buğday",
            "confidence_score": 85.5,
            "probability": 0.855
        },
        {
            "plant_name": "Arpa",
            "confidence_score": 78.2,
            "probability": 0.782
        }
        // ... diğer öneriler
    ],
    "model_info": {
        "model_type": "RandomForestClassifier",
        "feature_count": 37,
        "recommendation_count": 5
    }
}
```

## Test

API'yi test etmek için:

```bash
python Backend/API/MachineLearning/test_ml_api.py
```

## Model Bilgileri

### Model Dosyası Formatı

Model dosyası (`model.pkl`) şu yapıda kaydedilmiştir:

```python
{
    'model': MultiOutputClassifier,      # Asıl ML modeli
    'scaler': StandardScaler,            # Veri normalizasyonu
    'metadata': {...}                    # Model hakkında bilgiler
}
```

API otomatik olarak bu yapıyı tanır ve:
- **Model**: Tahminler için kullanılır
- **Scaler**: Veri normalizasyonu için kullanılır  
- **Metadata**: Model bilgileri için kullanılır

### Eğitim Verileri

Model şu değişkenlerle eğitildi:

**Toprak Özellikleri:**
- `wrb4_code`: Toprak sınıflandırması
- `physical_available_water_capacity`: Su tutma kapasitesi
- `basic_organic_carbon`: Organik karbon
- `basic_c/n_ratio`: C/N oranı
- `texture_clay`: Kil oranı
- `texture_sand`: Kum oranı
- `texture_coarse_fragments`: Kaba parçacık oranı
- `physical_reference_bulk_density`: Referans hacim yoğunluğu
- `chemical_cation_exchange_capacity`: Katyon değişim kapasitesi
- `chemical_clay_cec`: Kil CEC
- `chemical_total_exchangeable_bases`: Toplam değişebilir bazlar
- `chemical_base_saturation`: Baz doygunluğu
- `chemical_exchangeable_sodium_percentage`: Değişebilir sodyum yüzdesi
- `chemical_aluminum_saturation`: Alüminyum doygunluğu
- `salinity_electrical_conductivity`: Elektriksel iletkenlik
- `salinity_total_carbon_equivalent`: Toplam karbon eşdeğeri
- `salinity_gypsum_content`: Jips içeriği

**İklim Özellikleri:**
- Sıcaklık verileri (Eylül, Aralık, Ağustos)
- Güneşlenme süreleri (Ağustos, Aralık)
- Yağışlı gün sayıları (Şubat-Mart-Nisan-Ağustos-Kasım-Yıllık)
- Yağış miktarları (Nisan-Aralık arası aylar + Yıllık)

### Hedef Bitkiler

Model 38 farklı bitki türü için tahmin yapar:

- Tahıllar: Arpa, Buğday, Mısır, Pirinç
- Endüstriyel: Pamuk, Ayçiçeği, Şeker Pancarı, Tütün
- Meyveler: Elma, Kayısı, Kiraz, Kivi, Muz, Şeftali, İncir, Üzüm
- Sebzeler: Domates, Biber, Patates, Patlıcan, Sarımsak
- Baklagiller: Fasulye, Mercimek, Nohut, Yer Fıstığı
- Diğer: Zeytin, Çay, Çilek, Badem, Ceviz, Fındık, Fıstık, Gül, Haşhaş

## Hata Yönetimi

API kapsamlı hata yakalama ve loglama sağlar:

- **Dosya Bulunamadı**: Model veya veri dosyaları eksikse
- **API Bağlantı Hatası**: SoilType API'ye erişim sorunu
- **Veri Format Hatası**: Geçersiz koordinat veya veri formatı
- **Model Hatası**: Tahmin sırasında oluşan hatalar
- **Model Dosyası Bozuk**: Model.pkl dosyası bozuksa fallback mode aktif olur

### Fallback Mode

Model dosyası bozuk olduğunda API otomatik olarak fallback mode'a geçer:

- **Kurallar Tabanlı Öneriler**: Basit kurallar kullanarak bitki önerileri yapar
- **Toprak Tipi Analizi**: WRB4 kodlarına göre öneriler
- **İklim Koşulları**: Sıcaklık ve yağış verilerine göre ayarlama
- **Güvenilir Sonuçlar**: Her zaman çalışır durumda kalır

Fallback mode durumunda API yanıtında `"fallback_mode": true` ve `"model_status": "Corrupted - Using fallback rules"` bilgileri yer alır.

Tüm hatalar detaylı loglama ile kaydedilir ve kullanıcıya anlamlı hata mesajları döndürülür.

## Geliştirme Notları

### Koordinat Eşleştirme

Şu anda koordinat-iklim eşleştirmesi basit bir rastgele örnekleme ile yapılmaktadır. Gerçek uygulamada:

1. Koordinat veritabanı oluşturulmalı
2. En yakın komşu algoritması kullanılmalı
3. İklim verileri gerçek zamanlı API'lerden alınmalı

### Model Güncelleme

Model güncellemek için:

1. Yeni eğitim verilerini hazırla
2. Modeli yeniden eğit
3. `Model/model.pkl` dosyasını güncelle
4. API'yi yeniden başlat

### Performans Optimizasyonu

- Model önbellekleme
- Asenkron API çağrıları
- Veritabanı optimizasyonu
- Paralel işleme