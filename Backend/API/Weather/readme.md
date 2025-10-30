# Hava Durumu API (Weather API) - router.py

Bu FastAPI router (`router.py`), Open-Meteo API'lerini kullanarak hava durumu verilerini almak için endpoint'ler sağlar. Günlük tahmin, saatlik tahmin ve geçmiş tarihli verileri destekler. Konum belirleme, kullanıcının IP adresinden otomatik olarak veya manuel koordinat girişi (enlem/boylam) ile yapılabilir.


## Önemli Özellikler

- **Asenkron İstekler:** Dış API çağrıları, FastAPI'nin asenkron yapısına uygun olarak `httpx` kütüphanesi ile non-blocking (bloke etmeyen) bir şekilde yapılır.
- **Redis Önbelleğe Alma (Caching):** Dış API'ye giden istekleri en aza indirmek ve performansı dramatik olarak artırmak için `fastapi-cache2` kütüphanesi kullanılır.

## GEREKSİNİMLER

Bu API modülünün düzgün çalışması için **çalışan bir Redis sunucusuna** ihtiyaç vardır(Redis olmasa da çalışır. Sadece Cache işlemi yapılmaz).

Ana `main.py` dosyası, Redis'e `redis://localhost:6379` adresi üzerinden bağlanacak şekilde yapılandırılmıştır.

### Hata Ayıklama: `ConnectionError`
Eğer uygulama loglarında `redis.exceptions.ConnectionError: ... [Errno 10061] Connect call failed` gibi bir hata görüyorsanız, bu durum **Redis sunucunuzun çalışmadığı** anlamına gelir.

**Çözüm:** Redis sunucunuzu başlatın. Eğer Docker kullanıyorsanız, aşağıdaki komutla hızlıca bir Redis container'ı başlatabilirsiniz:
```bash
docker run -d -p 6379:6379 redis
```

## Önbelleğe Alma (Caching) Mantığı

Dış API'ye yapılan pahalı istekler, Redis üzerinde şu sürelerle önbelleğe alınır:

- **Saatlik Tahmin (`get_hourly_Data`):** 1 Saat (3600 saniye)
- **Günlük Tahmin (`get_daily_Data`):** 1 Saat (3600 saniye)
- **Geçmiş Veri (`get_data_by_date`):** 24 Saat (86400 saniye)

Cache'leme sayesinde, aynı koordinatlar için 1 saat içinde gelen binlerce istek, Open-Meteo API'sine hiç gitmeden, milisaniyeler içinde doğrudan Redis'ten yanıtlanır.



## Veri Modelleri (Pydantic)

API, istek gövdelerini doğrulamak için aşağıdaki Pydantic modellerini kullanır:

### `ManualRequest`

Manuel olarak enlem ve boylam bilgisi sağlamak için kullanılır.

* `method: str`: Yöntem tipi. Validasyon gereği "Manual" olmalıdır.
* `longitude: float`: Boylam değeri (-180 ile 180 arası).
* `latitude: float`: Enlem değeri (-90 ile 90 arası).
* *Validasyon*: Koordinatların sayısal ve geçerli aralıkta olduğunu, ayrıca SQL injection gibi temel güvenlik risklerine karşı (sadece sayı, '.', '-' içermeli) kontrol eder.

### `AutoRequest`

Otomatik konum tespiti (IP tabanlı) kullanılacağında kullanılır.

* `method: str`: Yöntem tipi. Validasyon gereği "Auto" olmalıdır.
* `day: int`: Gün sayısı (1-16 arası, varsayılan 1). *Not: Bu modeldeki `day` alanı, asıl gün sayısını belirten `days` query parametresi ile birlikte kullanılır.*

## Yardımcı Fonksiyonlar

* `get_automatic_coordinates()`: `geocoder` kütüphanesini kullanarak istek atan kullanıcının IP adresinden (enlem, boylam) koordinatlarını tespit eder.
* `get_hourly_Data()`: Open-Meteo **forecast** API'sinden belirtilen koordinatlar ve gün sayısı için saatlik hava durumu verilerini (yağış, sıcaklık, nem, toprak nemi/sıcaklığı, rüzgar vb.) çeker.
* `get_daily_Data()`: Open-Meteo **forecast** API'sinden belirtilen koordinatlar ve gün sayısı için günlük hava durumu verilerini (yağış toplamı, ortalama sıcaklık, buharlaşma, rüzgar vb.) çeker.
* `get_data_by_date()`: Open-Meteo **archive** API'sinden belirtilen koordinatlar ve tarih aralığı için geçmiş günlük hava durumu verilerini çeker.
* `_validate_dates()`: Başlangıç tarihinin bitiş tarihinden önce olduğunu ve bitiş tarihinin çok (16 günden fazla) gelecekte olmadığını doğrular.
* `WMO_CODES_TR`: API'den gelen sayısal WMO (World Meteorological Organization) hava durumu kodlarını, "Açık", "Parçalı Bulutlu", "Yağmur (Hafif)" gibi Türkçe metinlere çeviren bir sözlüktür.

---

## API Endpoint'leri

Tüm endpoint'ler `/weather` prefix'i altındadır.

### 1. Günlük Hava Durumu (Otomatik Konum)

* **Endpoint:** `POST /weather/dailyweather/auto`
* **Açıklama:** İstek atan kullanıcının IP adresinden konumunu otomatik olarak tespit eder ve belirtilen gün sayısı (1-16) kadar günlük hava durumu tahmini sağlar.
* **Request Body:** `AutoRequest` modeli.
* **Query Parametresi:** `days: int` (Varsayılan: 1, Min: 1, Max: 16) - Kaç günlük tahmin alınacağını belirtir.
* **Dönen Değer (Başarılı):** Günlük verileri ve koordinatları içeren bir liste (`List[dict]`).
    * *Örnek:* `[{"day": "2023-10-27", "temperature_2m_mean": 15.5, ...}, {"coordinates": {"longitude": 28.98, "latitude": 41.01}}, ...]`
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Konum tespit edilemedi"}` veya `{"error": "Hava durumu verisi alınamadı"}`

### 2. Günlük Hava Durumu (Manuel Konum)

* **Endpoint:** `POST /weather/dailyweather/manual`
* **Açıklama:** Request body'de sağlanan enlem/boylam koordinatlarına göre belirtilen gün sayısı (1-16) kadar günlük hava durumu tahmini sağlar.
* **Request Body:** `ManualRequest` modeli.
* **Query Parametresi:** `days: int` (Varsayılan: 1, Min: 1, Max: 16) - Kaç günlük tahmin alınacağını belirtir.
* **Dönen Değer (Başarılı):** Günlük verileri ve koordinatları içeren bir liste (`List[dict]`).
    * *Örnek:* `[{"day": "2023-10-27", "temperature_2m_mean": 15.5, ...}, {"coordinates": {"longitude": 28.98, "latitude": 41.01}}, ...]`
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Hava durumu verisi alınamadı"}`

### 3. Geçmiş Günlük Hava Durumu (Manuel Konum)

* **Endpoint:** `POST /weather/dailyweather/bydate/manual/{start_date}/{end_date}`
* **Açıklama:** Belirtilen koordinatlar için belirtilen tarih aralığındaki (YYYY-AA-GG formatında) geçmiş günlük hava durumu verilerini döndürür.
* **Path Parametreleri:**
    * `start_date: date` (Format: YYYY-AA-GG)
    * `end_date: date` (Format: YYYY-AA-GG)
* **Request Body:** `ManualRequest` modeli.
* **Dönen Değer (Başarılı):** Günlük verileri ve koordinatları içeren bir liste (`List[dict]`).
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Hava durumu verisi alınamadı"}` veya `{"error": "start_date must be <= end_date"}`

### 4. Geçmiş Günlük Hava Durumu (Otomatik Konum)

* **Endpoint:** `POST /weather/dailyweather/bydate/auto/{start_date}/{end_date}`
* **Açıklama:** IP adresinden tespit edilen konum için belirtilen tarih aralığındaki (YYYY-AA-GG formatında) geçmiş günlük hava durumu verilerini döndürür.
* **Path Parametreleri:**
    * `start_date: date` (Format: YYYY-AA-GG)
    * `end_date: date` (Format: YYYY-AA-GG)
* **Request Body:** `AutoRequest` modeli.
* **Dönen Değer (Başarılı):** Günlük verileri ve koordinatları içeren bir liste (`List[dict]`).
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Konum tespit edilemedi"}` veya `{"error": "Hava durumu verisi alınamadı"}`

### 5. Saatlik Hava Durumu (Otomatik Konum)

* **Endpoint:** `POST /weather/hourlyweather/auto`
* **Açıklama:** IP adresinden tespit edilen konuma göre belirtilen gün sayısı (1-16) kadar saatlik hava durumu tahmini verir.
* **Request Body:** `AutoRequest` modeli.
* **Query Parametresi:** `days: int` (Varsayılan: 1, Min: 1, Max: 16) - Kaç günlük tahmin alınacağını belirtir.
* **Dönen Değer (Başarılı):** Saatlik verileri ve koordinatları içeren bir liste (`List[dict]`).
    * *Örnek:* `[{"time": "2023-10-27T12:00", "temperature_2m": 16.2, ...}, {"coordinates": {"longitude": 28.98, "latitude": 41.01}}, ...]`
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Konum tespit edilemedi"}` veya `{"error": "Hava durumu verisi alınamadı"}`

### 6. Saatlik Hava Durumu (Manuel Konum)

* **Endpoint:** `POST /weather/hourlyweather/manual`
* **Açıklama:** Sağlanan enlem/boylam koordinatlarına göre belirtilen gün sayısı (1-16) kadar saatlik hava durumu tahmini verir.
* **Request Body:** `ManualRequest` modeli.
* **Query Parametresi:** `days: int` (Varsayılan: 1, Min: 1, Max: 16) - Kaç günlük tahmin alınacağını belirtir.
* **Dönen Değer (Başarılı):** Saatlik verileri ve koordinatları içeren bir liste (`List[dict]`).
    * *Örnek:* `[{"time": "2023-10-27T12:00", "temperature_2m": 16.2, ...}, {"coordinates": {"longitude": 28.98, "latitude": 41.01}}, ...]`
* **Dönen Değer (Hata):** Hata mesajı içeren bir sözlük (`dict`).
    * *Örnek:* `{"error": "Hava durumu verisi alınamadı"}`