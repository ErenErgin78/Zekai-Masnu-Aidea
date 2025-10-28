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
- **Toprak Analizi API:** `/soiltype/analyze` ile koordinatlardan toprak bilgisi
- **Hava Durumu API:** `/weather/` altındaki uçlarla meteorolojik veriler
- **ML Öneri API:** `/ml/analyze` ile toprak+iklim verisine göre ürün önerisi
- **RAG Bilgi**: PDF/doküman tabanlı bilgi çıkarımı (LLM üzerinden kullanılır)

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
- **Chat Paneli:** Kullanıcı mesajları ve AI yanıtları için ana sohbet ekranı
- **Analiz Paneli:** Toprak, hava durumu ve ML sonuçlarının görselleştirildiği alan
- **API Bağlantısı:** FastAPI backend'e HTTP istekleri ile veri alışverişi
- **Responsive Tasarım:** Mobil ve masaüstü cihazlarda uyumlu çalışma

## 🔄 Sistem Akışı

1. **Kullanıcı** arayüzden soru veya veri girer
2. **LLM** sorguyu analiz eder
3. **İlgili backend modülleri** çalıştırılır (örneğin ürün tahmini veya hava durumu)
4. **RAG sistemi** gerekirse bilgi sağlar
5. **LLM** tüm sonuçları birleştirerek kullanıcıya yanıt verir

## 🌾 Makine Öğrenmesi ile Ürün Önerisi (Güncel)

- Artık sistem, toprak ve iklim verilerini birleştirerek makine öğrenmesi modeliyle ürün önerileri sunar.
- LLM, kullanıcı “burada hangi bitki yetişir?” gibi sorular sorduğunda otomatik olarak ML aracını kullanır.
- Konum alma her zaman otomatik yapılır; manuel koordinat gerektirmez.
- Başlıca özellikler:
  - Toprak verisi: SoilType API’den alınır
  - İklim verisi: dahili veri/varsayılanlar ile tamamlanır
  - Model: arka planda yüklü ML modeli; gerekli durumlarda güvenli kural tabanlı öneriye düşer
  - Çıktı: “Makine öğrenmesi modeli, toprak ve iklim verilerine göre şu bitkileri önerdi” formatında, güven skorlarıyla birlikte

### Çalıştırma ve Entegrasyon

- LLM başlarken Soil+Weather API (8000) ve ML API (8003) otomatik başlatılır.
- Frontend/LLM tarafı, ML aracını bir “tool” olarak görür ve gerektiğinde çağırır.
- Kullanıcı ek ayar yapmadan “hangi ürün yetişir?” gibi sorulara doğrudan öneri alır.

### Kısa Notlar

- ML API rota özeti: `POST /ml/analyze` (arka planda LLM tarafından kullanılır)
- Güvenli çalışma: Servisler geç cevap verirse kısa zaman aşımları ve otomatik geri dönüşler uygulanır.

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

## 🤖 Backend Makine Öğrenmesi (Özet)

- Ürün önerisi, toprak (SoilType API) ve iklim özellikleri birlikte değerlendirilerek yapılır.
- LLM, kullanıcı sorusuna göre ML aracını otomatik çağırır; konum otomatik alınır.
- Model arka planda yüklenir; gerekirse güvenli kural tabanlı öneriyle yanıt verir.
- Amaç: “Bu bölgede hangi ürünler yetişir?” sorusuna hızlı, anlaşılır ve uygulanabilir öneriler sunmak.

## 🔗 Entegrasyon Mantığı

- Tüm bileşenler bir merkezi yönetici modül tarafından koordine edilir
- Modüller arası iletişim API tabanlıdır
- Veri akışı sıralı şekilde ilerler: **Kullanıcı → LLM → Backend/RAG → LLM → Kullanıcı**

## ⚠️ Önemli Not

Proje yalnızca yazılım ve yapay zeka temelli bir sistemdir; gerçek sensör, fiziksel cihaz veya saha ekipmanı bulunmaz. Tüm veriler dijital kaynaklardan (API, veri seti, doküman) alınır ve simülasyon mantığıyla işlenir.

---

**AIDEA** ile tarımınızı akıllı hale getirin! 🌱🤖