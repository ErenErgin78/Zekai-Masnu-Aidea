# 🌍 Soil Analysis API

HWSD2 (Harmonized World Soil Database) veritabanını kullanarak toprak analizi yapan FastAPI servisi.

## 🚀 Kurulum

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Gerekli Dosyalar
- `HWSD2.bil` - Raster harita dosyası
- `HWSD2.mdb` - Veritabanı dosyası
- `HWSD2.hdr` - Header dosyası (opsiyonel)

## 🏃‍♂️ Çalıştırma

### **API'yi Başlatma**

#### **1. Gerekli Dosyaları Kontrol Edin:**
```bash
# Proje dizininde şu dosyaların olduğundan emin olun:
ls HWSD2.bil HWSD2.mdb HWSD2.hdr
```

#### **2. API'yi Başlatın:**
```bash
python soil_api.py
```

#### **3. Başarılı Başlatma Mesajları:**
```
2025-10-16 23:55:15,591 - __main__ - INFO - Soil Analysis Service initialized successfully
INFO:     Started server process [22348]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### **4. API Erişim Noktaları:**
- **Ana URL**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### **API Başlatma Sorunları ve Çözümleri:**

#### **Port 8000 Kullanımda Hatası:**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Çözüm:**
```bash
# Port 8000'i kullanan process'i bul
netstat -ano | findstr :8000

# Process'i sonlandır (PID'yi değiştirin)
taskkill /PID [PID] /F

# API'yi tekrar başlat
python soil_api.py
```

#### **NumPy Uyumluluk Hatası:**
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.3.4
```

**Çözüm:**
```bash
# NumPy'yi downgrade et
pip install "numpy<2.0.0" --force-reinstall

# API'yi başlat
python soil_api.py
```


### **API Başlatma Kontrolü:**

#### **1. Health Check:**
```bash
curl http://localhost:8000/health
```

#### **2. PowerShell ile Test:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

#### **3. Browser ile Test:**
- http://localhost:8000/docs adresini açın
- Swagger UI'da "Try it out" butonlarını kullanın

### 🚀 Hızlı Test
```bash
# API'yi başlat
python soil_api.py

# Başka terminal'de test et
curl http://localhost:8000/health
```

## 🧪 Test Script Kullanımı

### **İnteraktif Test Script**
```bash
python test_api.py
```

Bu script size şu seçenekleri sunar:
1. **Manuel koordinat girişi** - Kendi koordinatlarınızı girin
2. **Otomatik konum tespiti** - IP adresinizden konum tespit eder
3. **Çıkış** - Test scriptini sonlandırır

### **Test Script Özellikleri:**
- ✅ **İnteraktif menü** - Kolay kullanım
- ✅ **Koordinat doğrulama** - Geçersiz koordinatları reddeder
- ✅ **Ham JSON gösterimi** - API response'unu tam olarak gösterir
- ✅ **Hata yönetimi** - Bağlantı ve zaman aşımı hatalarını yakalar
- ✅ **Özet bilgiler** - Toprak analizi sonuçlarını özetler

### **Test Script Kullanım Adımları:**

#### **1. API'yi Başlatın:**
```bash
python soil_api.py
```

#### **2. Test Script'i Çalıştırın:**
```bash
python test_api.py
```

#### **3. Menüden Seçim Yapın:**
```
🌍 Soil Analysis API Test
========================================
Analiz yöntemini seçin:
1. Manuel koordinat girişi
2. Otomatik konum tespiti
3. Çıkış

Seçiminiz (1-3): 
```

#### **4. Manuel Koordinat Girişi (Seçenek 1):**
```
📍 Manuel Koordinat Girişi
------------------------------
Boylam (Longitude) girin (-180 ile 180 arası): 32.0
Enlem (Latitude) girin (-90 ile 90 arası): 39.0
✅ Koordinatlar alındı: Boylam=32, Enlem=39
```

#### **5. Otomatik Konum Tespiti (Seçenek 2):**
```
🌐 Otomatik Konum Tespiti
------------------------------
Konumunuz algılanıyor... (Bu işlem biraz sürebilir)
✅ Konum algılandı: Enlem=49, Boylam=1
(Not: Bu konum, IP adresinize dayalı bir tahmindir.)
(Koordinatlar tam sayı formatında yuvarlanmıştır.)
```

#### **6. Test Sonuçları:**
```
🧪 Manuel Analiz Testi
📍 Koordinatlar: Boylam=32, Enlem=39
--------------------------------------------------
📤 Gönderilen JSON: {
  "method": "Manual",
  "longitude": 32,
  "latitude": 39
}
📊 HTTP Status: 200
✅ Başarılı!

📋 Ham JSON Response:
==================================================
{
  "success": true,
  "message": "Soil analysis completed successfully",
  "timestamp": "2024-01-01T12:00:00",
  "coordinates": {
    "longitude": 32,
    "latitude": 39
  },
  "soil_id": 1849,
  "classification": {
    "wrb4_code": "CMca",
    "wrb4_description": "Cambisols - Moderately developed soils",
    "wrb2_code": "CM",
    "wrb2_description": "Cambisols - Moderately developed soils",
    "fao90_code": "CMc"
  },
  "basic_properties": [...],
  "texture_properties": [...],
  "physical_properties": [...],
  "chemical_properties": [...],
  "salinity_properties": [...]
}
==================================================

📊 Özet Bilgiler:
   🆔 Soil ID: 1849
   🌍 WRB4: CMca - Cambisols - Moderately developed soils
   🌍 WRB2: CM - Cambisols - Moderately developed soils
   🌍 FAO90: CMc
```

### **Test Script Hata Mesajları:**

#### **API Çalışmıyor:**
```
🔌 Bağlantı hatası! API çalışıyor mu?
```

#### **Geçersiz Koordinatlar:**
```
❌ Geçersiz koordinat: Boylam -180 ile 180 arasında olmalıdır
```

#### **Zaman Aşımı:**
```
⏰ Zaman aşımı!
```

#### **Otomatik Konum Tespiti Başarısız:**
```
❌ Konumunuz otomatik olarak algılanamadı.
```

## 📋 **Tam Kullanım Rehberi**

### **Adım 1: Proje Hazırlığı**
```bash
# 1. Proje dizinine gidin
cd "C:\Users\Eren\Desktop\Stuff\Kairu\Aidea\Soil Map\MapPy"

# 2. Gerekli dosyaları kontrol edin
ls HWSD2.bil HWSD2.mdb HWSD2.hdr soil_api.py test_api.py

# 3. Python dependencies'leri yükleyin
pip install -r requirements.txt
```

### **Adım 2: API'yi Başlatın**
```bash
# Terminal 1: API'yi başlat
python soil_api.py
```

**Başarılı başlatma çıktısı:**
```
2025-10-16 23:55:15,591 - __main__ - INFO - Soil Analysis Service initialized successfully
INFO:     Started server process [22348]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Adım 3: Test Script'i Çalıştırın**
```bash
# Terminal 2: Test script'i başlat
python test_api.py
```

### **Adım 4: İnteraktif Test Menüsü**
```
🌍 Soil Analysis API Test
========================================
Analiz yöntemini seçin:
1. Manuel koordinat girişi
2. Otomatik konum tespiti
3. Çıkış

Seçiminiz (1-3): 
```

### **Adım 5: Test Seçenekleri**

#### **Seçenek 1: Manuel Koordinat Girişi**
```
📍 Manuel Koordinat Girişi
------------------------------
Boylam (Longitude) girin (-180 ile 180 arası): 32.0
Enlem (Latitude) girin (-90 ile 90 arası): 39.0
✅ Koordinatlar alındı: Boylam=32, Enlem=39

🧪 Manuel Analiz Testi
📍 Koordinatlar: Boylam=32, Enlem=39
--------------------------------------------------
📤 Gönderilen JSON: {
  "method": "Manual",
  "longitude": 32,
  "latitude": 39
}
📊 HTTP Status: 200
✅ Başarılı!

📋 Ham JSON Response:
==================================================
{
  "success": true,
  "message": "Soil analysis completed successfully",
  "timestamp": "2024-01-01T12:00:00",
  "coordinates": {
    "longitude": 32,
    "latitude": 39
  },
  "soil_id": 1849,
  "classification": {
    "wrb4_code": "CMca",
    "wrb4_description": "Cambisols - Moderately developed soils",
    "wrb2_code": "CM",
    "wrb2_description": "Cambisols - Moderately developed soils",
    "fao90_code": "CMc"
  },
  "basic_properties": [...],
  "texture_properties": [...],
  "physical_properties": [...],
  "chemical_properties": [...],
  "salinity_properties": [...]
}
==================================================

📊 Özet Bilgiler:
   🆔 Soil ID: 1849
   🌍 WRB4: CMca - Cambisols - Moderately developed soils
   🌍 WRB2: CM - Cambisols - Moderately developed soils
   🌍 FAO90: CMc
```

#### **Seçenek 2: Otomatik Konum Tespiti**
```
🌐 Otomatik Konum Tespiti
------------------------------
Konumunuz algılanıyor... (Bu işlem biraz sürebilir)
✅ Konum algılandı: Enlem=49, Boylam=1
(Not: Bu konum, IP adresinize dayalı bir tahmindir.)
(Koordinatlar tam sayı formatında yuvarlanmıştır.)

🌐 Otomatik Analiz Testi
--------------------------------------------------
📤 Gönderilen JSON: {
  "method": "Auto"
}
📊 HTTP Status: 200
✅ Başarılı!

📋 Ham JSON Response:
==================================================
[API response JSON'u burada görünür]
==================================================

📊 Özet Bilgiler:
   📍 Koordinatlar: Boylam=1, Enlem=49
   🆔 Soil ID: [Soil ID]
   🌍 WRB4: [WRB4 Code] - [Description]
   🌍 WRB2: [WRB2 Code] - [Description]
   🌍 FAO90: [FAO90 Code]
```

### **Adım 6: Test Tamamlama**
```
Başka bir test yapmak ister misiniz? (e/h): h

👋 Test tamamlandı!
```

## 🔧 **Sorun Giderme**

### **API Başlatılamıyor:**
1. Port 8000'in boş olduğundan emin olun
2. Gerekli dosyaların mevcut olduğunu kontrol edin
3. Python dependencies'lerin yüklü olduğunu kontrol edin

### **Test Script Çalışmıyor:**
1. API'nin çalıştığından emin olun
2. İnternet bağlantınızı kontrol edin (otomatik konum için)
3. Koordinat sınırlarını kontrol edin

### **JSON Response Boş:**
1. Veritabanı dosyalarının doğru konumda olduğunu kontrol edin
2. Koordinatların geçerli aralıkta olduğunu kontrol edin
3. API log'larını kontrol edin

## 📖 Postman Test Koleksiyonu

### 🔧 Postman Kurulumu

#### Hızlı Kurulum:
1. **Collection Import**: `postman_collection.json` dosyasını Postman'a import edin
2. **Environment Import**: `postman_environment.json` dosyasını Postman'a import edin
3. **Environment Seç**: "Soil Analysis Environment" seçin
4. **Test Et**: Collection'daki request'leri çalıştırın

#### Manuel Kurulum:
1. **Postman Collection** oluşturun
2. **Environment** oluşturun: `base_url = http://localhost:8000`
3. Aşağıdaki request'leri ekleyin

### 📋 Test Request'leri

#### 1. Health Check
```http
GET {{base_url}}/health
```

#### 2. Manuel Koordinat Analizi
```http
POST {{base_url}}/analyze
Content-Type: application/json

{
    "method": "Manual",
    "longitude": 1.0,
    "latitude": 49.0
}
```

#### 3. Otomatik Konum Tespiti
```http
POST {{base_url}}/analyze/auto
Content-Type: application/json

{
    "method": "Auto"
}
```

### 🧪 Test Koordinatları

#### Avrupa Test Koordinatları:
```json
{
    "method": "Manual",
    "longitude": 1.0,
    "latitude": 49.0
}
```

#### Türkiye Test Koordinatları:
```json
{
    "method": "Manual",
    "longitude": 32.0,
    "latitude": 39.0
}
```

#### Amerika Test Koordinatları:
```json
{
    "method": "Manual",
    "longitude": -74.0,
    "latitude": 40.0
}
```

#### Asya Test Koordinatları:
```json
{
    "method": "Manual",
    "longitude": 120.0,
    "latitude": 30.0
}
```

### 📊 Örnek Response

#### Başarılı Analiz Response:
```json
{
    "success": true,
    "message": "Soil analysis completed successfully",
    "timestamp": "2024-01-01T12:00:00",
    "coordinates": {
        "longitude": 1.0,
        "latitude": 49.0
    },
    "soil_id": 1849,
    "classification": {
        "wrb4_code": "CMca",
        "wrb4_description": "Cambisols - Moderately developed soils",
        "wrb2_code": "CM",
        "wrb2_description": "Cambisols - Moderately developed soils",
        "fao90_code": "CMc"
    },
    "basic_properties": [
        {
            "name": "pH",
            "value": 8.2,
            "unit": "pH units"
        }
    ],
    "texture_properties": [
        {
            "name": "Clay",
            "value": 18,
            "unit": "%"
        }
    ],
    "physical_properties": [
        {
            "name": "Bulk Density",
            "value": 1.45,
            "unit": "g/cm³"
        }
    ],
    "chemical_properties": [
        {
            "name": "Cation Exchange Capacity",
            "value": 14,
            "unit": "cmol/kg"
        }
    ],
    "salinity_properties": [
        {
            "name": "Electrical Conductivity",
            "value": 1,
            "unit": "dS/m"
        }
    ]
}
```

#### Hata Response:
```json
{
    "detail": "Invalid coordinates: longitude must be between -180 and 180"
}
```

## 🔧 API Endpoints

### 1. Manuel Koordinat Analizi
```http
POST /analyze
Content-Type: application/json

{
    "method": "Manual",
    "longitude": 1.0,
    "latitude": 49.0
}
```

### 2. Otomatik Konum Tespiti
```http
POST /analyze/auto
Content-Type: application/json

{
    "method": "Auto"
}
```

### 3. Sağlık Kontrolü
```http
GET /health
```

## 📊 Yanıt Formatı

```json
{
    "success": true,
    "message": "Soil analysis completed successfully",
    "timestamp": "2024-01-01T12:00:00",
    "coordinates": {
        "longitude": 1.0,
        "latitude": 49.0
    },
    "soil_id": 1849,
    "classification": {
        "wrb4_code": "CMca",
        "wrb4_description": "Cambisols - Moderately developed soils",
        "wrb2_code": "CM",
        "wrb2_description": "Cambisols - Moderately developed soils",
        "fao90_code": "CMc"
    },
    "basic_properties": [
        {
            "name": "pH",
            "value": 8.2,
            "unit": "pH units"
        }
    ],
    "texture_properties": [
        {
            "name": "Clay",
            "value": 18,
            "unit": "%"
        }
    ],
    "physical_properties": [
        {
            "name": "Bulk Density",
            "value": 1.45,
            "unit": "g/cm³"
        }
    ],
    "chemical_properties": [
        {
            "name": "Cation Exchange Capacity",
            "value": 14,
            "unit": "cmol/kg"
        }
    ],
    "salinity_properties": [
        {
            "name": "Electrical Conductivity",
            "value": 1,
            "unit": "dS/m"
        }
    ]
}
```

## 🛡️ Güvenlik Özellikleri

### 1. Input Validation
- Koordinat sınırları: -180 ≤ longitude ≤ 180, -90 ≤ latitude ≤ 90
- Method validation: Sadece "Manual" veya "Auto" kabul edilir
- SQL injection koruması: Sadece sayısal değerlere izin verilir

### 2. Error Handling
- Kapsamlı exception handling
- Detaylı hata mesajları
- Logging sistemi

### 3. Data Sanitization
- Koordinatlar otomatik yuvarlanır
- Geçersiz karakterler filtrelenir
- Veritabanı sorguları parametrize edilir

## 🔍 Kullanım Örnekleri

### Python ile Kullanım
```python
import requests

# Manuel analiz
response = requests.post("http://localhost:8000/analyze", json={
    "method": "Manual",
    "longitude": 1.0,
    "latitude": 49.0
})

result = response.json()
print(f"Soil ID: {result['soil_id']}")
print(f"WRB4: {result['classification']['wrb4_code']}")
```

### cURL ile Kullanım
```bash
# Manuel analiz
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"method": "Manual", "longitude": 1.0, "latitude": 49.0}'

# Otomatik analiz
curl -X POST "http://localhost:8000/analyze/auto" \
     -H "Content-Type: application/json" \
     -d '{"method": "Auto"}'
```

## 📝 Logging

API detaylı logging sağlar:
- INFO: Normal işlemler
- WARNING: Uyarılar
- ERROR: Hatalar

Log formatı:
```
2024-01-01 12:00:00 - soil_api - INFO - Soil ID found from raster: 1849
```

## 🚨 Hata Kodları

- **200**: Başarılı
- **400**: Geçersiz istek
- **404**: Toprak verisi bulunamadı
- **422**: Validation hatası
- **500**: Sunucu hatası
- **503**: Servis kullanılamıyor

## 🔧 Geliştirme

### Yeni Özellik Ekleme
1. `SoilAnalysisService` sınıfına yeni method ekle
2. Pydantic modeli güncelle
3. Endpoint ekle
4. Test yaz

### Debugging
```bash
# Debug modunda çalıştır
uvicorn soil_api:app --reload --log-level debug
```

## 📋 TODO

- [ ] Caching sistemi ekle
- [ ] Rate limiting ekle
- [ ] Authentication ekle
- [ ] Batch processing ekle
- [ ] Export functionality ekle

## 🤝 Katkıda Bulunma

1. Fork yap
2. Feature branch oluştur
3. Değişiklikleri commit et
4. Pull request gönder

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
