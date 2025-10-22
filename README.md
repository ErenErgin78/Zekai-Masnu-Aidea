# 🌱 AIDEA - Akıllı Tarım Asistanı

AIDEA, yapay zeka destekli tarım asistanıdır. Organik tarım, toprak analizi ve hava durumu konularında çiftçilere akıllı öneriler sunar.

## 🎯 Proje Amacı

AIDEA, modern tarım teknikleri ile geleneksel bilgiyi birleştirerek çiftçilere:
- **Toprak analizi** ve besin önerileri
- **Hava durumu** takibi ve iklim analizi  
- **Organik tarım** bilgi bankası
- **Akıllı öneriler** ve rehberlik

sunmaktadır.

## 🏗️ Sistem Mimarisi

Proje, tamamen yazılım tabanlı olup dört ana katmandan oluşan sanal bir mimariye sahiptir:

### 1. Backend (Arka Plan Sistemi)
- **Toprak Analizi Modülü:** Kullanıcının girdiği koordinat veya veri setine göre toprak tipi bilgilerini getirir (gerçek sensör bağlantısı yoktur, tamamen veri tabanı veya API üzerinden çalışır)
- **Hava Durumu Modülü:** Dış kaynak API'lerinden meteorolojik verileri çeker
- **Makine Öğrenmesi Modülü:** Tarımsal faktörlere göre uygun ürün tahminini yapar (Random Forest modeli)
- **Veri Görselleştirme Aracı:** Model sonuçlarını grafik veya tablo şeklinde gösterir

### 2. Bilgi Bankası (RAG – Retrieval Augmented Generation)
- Tarım, iklim, gübreleme ve organik üretim konularında dijital PDF/metin içeriklerini işler
- Kullanıcının sorusuna göre en ilgili bilgi parçasını bulur
- LLM'e bağlanarak bu bilgiyi doğal dille açıklar

### 3. Yapay Zeka Katmanı (LLM – Language Model Layer)
- **Model:** Google Gemini tabanlı dil modeli
- **İşlev:** Kullanıcının sorusunu yorumlar, gerekirse backend ve RAG modüllerinden veri ister
- **Zincirleme Mantık:** Örneğin "toprak analizi + hava durumu + ürün önerisi" adımlarını sıralı biçimde yürütür
- **Karar Verme:** Her adımda hangi aracın çalıştırılacağına kendisi karar verir

### 4. Frontend (Kullanıcı Arayüzü)
- Web tabanlı, mobil uyumlu bir sohbet ekranıdır
- Kullanıcı mesajlarını backend'e iletir ve yapay zekadan gelen yanıtları sunar
- Grafiksel analiz çıktıları da burada görüntülenir

## 🔄 Sistem Akışı

1. **Kullanıcı** arayüzden soru veya veri girer
2. **LLM** sorguyu analiz eder
3. **İlgili backend modülleri** çalıştırılır (örneğin ürün tahmini veya hava durumu)
4. **RAG sistemi** gerekirse bilgi sağlar
5. **LLM** tüm sonuçları birleştirerek kullanıcıya yanıt verir

## 🛠️ Teknolojiler

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gemini** - Yapay zeka modeli
- **ChromaDB** - Vektör veritabanı
- **HuggingFace** - Embedding modelleri
- **HWSD2** - Toprak veritabanı
- **Random Forest** - Makine öğrenmesi modeli

### Frontend  
- **HTML5, CSS3, JavaScript** - Modern web teknolojileri
- **Responsive Design** - Tüm cihazlarda uyumlu
- **Local Storage** - Veri saklama
- **Geolocation API** - Konum servisleri

### Veri Kaynakları
- **PDF Dokümanlar** - Organik tarım rehberleri
- **Hava Durumu API'leri** - Gerçek zamanlı veri
- **Toprak Veritabanı** - HWSD2 global toprak haritası
- **Akademik Makaleler** - Bilimsel kaynaklar

## 📦 Kurulum

### Gereksinimler
```bash
Python 3.8+
Git
```

### Adım 1: Projeyi İndirin
```bash
git clone https://github.com/ErenErgin78/Zekai-Masnu-Aidea.git
cd Zekai-Masnu-Aidea
```

### Adım 2: Backend Kurulumu
```bash
# Sanal ortam oluşturun
python -m venv env
source env/bin/activate  # Linux/Mac
# veya
env\Scripts\activate     # Windows

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### Adım 3: Ortam Değişkenleri
```bash
# .env dosyası oluşturun
GEMINI_API_KEY=your_gemini_api_key_here
```

### Adım 4: Sistemi Başlatın
```bash
# Terminal 1: Backend API'leri
cd Backend/API
python main.py

# Terminal 2: Ana Chatbot
cd LLM  
python main_chatbot.py
```

### Adım 5: Frontend'e Erişin
```
http://localhost:8001
```

## 🎮 Kullanım

### Chat Sistemi
1. **Ana sayfayı** açın
2. **Mesaj yazın** (örn: "Ankara'da hava nasıl?")
3. **AIDEA yanıtlar** ve öneriler sunar
4. **Sohbet geçmişi** otomatik kaydedilir

### Örnek Sorgular
- "Ankara'da hava durumu nasıl?"
- "Toprak analizi yap"
- "Organik tarım nedir?"
- "Bu toprakta hangi ürünler yetişir?"

### Sohbet Yönetimi
- **Yeni Sohbet** - Yeni konuşma başlatın
- **Sohbet Geçmişi** - Önceki konuşmaları görün
- **Sohbet Silme** - Gereksiz sohbetleri silin

## 🔧 Proje Yapısı

```
Zekai-Masnu-Aidea/
├── Backend/
│   ├── API/           # FastAPI servisleri
│   │   ├── SoilType/  # Toprak analizi
│   │   ├── Weather/   # Hava durumu
│   │   └── MachineLearning/ # ML modelleri
│   └── RAG/           # Bilgi bankası sistemi
├── LLM/               # Yapay zeka modelleri
│   ├── tools/         # Araçlar
│   ├── agents/        # Agent'lar
│   └── chains/        # Zincirler
├── Frontend/          # Web arayüzü
└── requirements.txt   # Python bağımlılıkları
```

## 🤖 Backend Makine Öğrenmesi

### Crop Recommendation Using Random Forest

**Problem Tanımı:** Bu projenin amacı, tarımsal faktörler (azot, fosfor, potasyum, sıcaklık, nem, pH, yağış miktarı) kullanılarak ekim yapılacak en uygun ürünün tahmin edilmesidir.

### Veri Kümesi Özeti

| Bilgi Türü | Açıklama |
|-------------|----------|
| **Toplam Satır (Gözlem)** | 2.200 |
| **Toplam Sütun (Değişken)** | 8 |
| **Bağımsız Değişkenler** | 7 adet (N, P, K, Temperature, Humidity, pH, Rainfall) |
| **Hedef Değişken** | Yetiştirilen ürün türü |
| **Farklı Etiket (Ürün) Sayısı** | 22 |

### Değişken Açıklamaları

| Değişken Adı | Açıklama |
|--------------|----------|
| **N** | Topraktaki azot miktarı |
| **P** | Topraktaki fosfor miktarı |
| **K** | Topraktaki potasyum miktarı |
| **Temperature** | Ortalama Sıcaklık (°C) |
| **Humidity** | Nem oranı (%) |
| **pH** | Toprak pH değeri |
| **Rainfall** | Yağış Miktarı (mm) |
| **Label** | Yetiştirilen ürün (hedef değişken) |

### Ürün Türleri (22 Adet)
rice, maize, chickpea, kidneybeans, pigeonpeas, mothbeans, mungbean, blackgram, lentil, pomegranate, banana, mango, grapes, watermelon, muskmelon, apple, orange, papaya, coconut, cotton, jute, coffee

### Veri Hazırlama Süreci

1. **Sütun İsimlerinin Standardizasyonu:** Tüm sütun adları küçük harfe çevrilmiş, boşluklar kaldırılmıştır
2. **Sayısal Dönüşümler:** Nokta (.) binlik ayırıcı, virgül (,) ise ondalık ayırıcı olarak düzeltilmiştir
3. **Aykırı Değer Analizi:** Her bir sayısal sütun için Z-score hesaplanmış, 3 standart sapmanın dışındaki veriler tespit edilmiştir
4. **Hedef Değişken Kontrolü:** label sütunu kategorik formata dönüştürülmüş ve sınıfların dengeli dağıldığı gözlemlenmiştir
5. **Korelasyon Analizi:** Değişkenler arası ilişkiler incelenmiş, en güçlü korelasyonun nem ve yağış arasında olduğu belirlenmiştir

### Analiz Yöntemi

**Random Forest Classifier** algoritması kullanılmıştır. Random Forest, birden fazla karar ağacını bir araya getirerek (ensemble) genelleme kabiliyeti yüksek bir model oluşturur.

**Kullanılan Adımlar:**
1. **Veri Ayrımı:** Veri %80 eğitim, %20 test olarak ayrılmıştır
2. **Model Eğitimi:** Random Forest Classifier ile model eğitilmiştir
3. **Performans Değerlendirmesi:** Çeşitli metriklerle model performansı ölçülmüştür

### Sonuçlar

- **Doğruluk Oranı:** %93'ün üzerinde
- **Model Performansı:** Yüksek genelleme kabiliyeti
- **Veri Kalitesi:** Eksik değer bulunmamıştır
- **Korelasyon:** Nem ve yağış arasında en güçlü ilişki

### İşlevsel Katkılar

- Tarım planlamasında çiftçilere doğru ürün önerileri sunabilir
- Sulama, gübreleme ve ekim zamanlamasının optimizasyonuna katkı sağlar
- Tarım politikalarının veri temelli kararlarla desteklenmesini mümkün kılar

### Kullanılan Araçlar

| Araç | Kullanım Amacı |
|-------|---------------|
| **Python** | Genel analiz ve modelleme |
| **pandas** | Veri işleme |
| **numpy** | Matematiksel işlemler |
| **matplotlib/seaborn** | Görselleştirme |
| **scikit-learn** | Makine öğrenmesi modeli ve metrikler |

## 🔗 Entegrasyon Mantığı

- Tüm bileşenler bir merkezi yönetici modül tarafından koordine edilir
- Modüller arası iletişim API tabanlıdır
- Veri akışı sıralı şekilde ilerler: **Kullanıcı → LLM → Backend/RAG → LLM → Kullanıcı**

## ⚠️ Önemli Not

Proje yalnızca yazılım ve yapay zeka temelli bir sistemdir; gerçek sensör, fiziksel cihaz veya saha ekipmanı bulunmaz. Tüm veriler dijital kaynaklardan (API, veri seti, doküman) alınır ve simülasyon mantığıyla işlenir.

---

**AIDEA** ile tarımınızı akıllı hale getirin! 🌱🤖