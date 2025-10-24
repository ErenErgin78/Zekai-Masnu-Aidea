# 🌾 LLM Toprak Analiz Sistemi

Akıllı toprak analizi ve tarımsal danışmanlık için geliştirilmiş, LLM destekli entegre bir sistem.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Mimari](#mimari)
- [Modüller](#modüller)
- [Konfigürasyon](#konfigürasyon)
- [Geliştirme](#geliştirme)

## 🎯 Genel Bakış

Bu proje, toprak verilerini analiz etmek, görselleştirmek ve kullanıcılara akıllı tarımsal öneriler sunmak için geliştirilmiş kapsamlı bir LLM (Large Language Model) uygulamasıdır. Sistem, GPS tabanlı otomatik konum tespiti, toprak analizi, hava durumu takibi ve RAG (Retrieval Augmented Generation) destekli bilgi bankası özellikleri sunar.

## ✨ Özellikler

- 🌍 **Otomatik Konum Tespiti**: Windows Konum Servisi, GPS ve IP tabanlı konum belirleme
- 🧪 **Toprak Analizi**: Detaylı toprak özelliklerinin analizi ve değerlendirmesi
- 📊 **Veri Görselleştirme**: Toprak verilerinin anlaşılır raporlara dönüştürülmesi
- 🌤️ **Gerçek Hava Durumu**: Open-Meteo API ile günlük/saatlik hava durumu tahminleri
- 📚 **RAG Bilgi Bankası**: Organik tarım bilgi tabanından akıllı sorgulama
- 🤖 **Akıllı Agentlar**: Araştırma ve analiz için özelleştirilmiş AI agentları
- 🔗 **Chain Sistemi**: Karmaşık analizler için zincirleme işlem akışları
- 🔄 **Birleşik Analiz**: Hava durumu + toprak analizi kombinasyonu

## 🚀 Kurulum

### Gereksinimler

- Python 3.8+
- Gemini API anahtarı
- Soil API (ayrı bir servis olarak çalışmalı)

### Adımlar

1. **Depoyu klonlayın**
```bash
git clone <repository-url>
cd LLM
```

2. **Gerekli paketleri yükleyin**
```bash
pip install -r requirements.txt
```

3. **Ortam değişkenlerini ayarlayın**
`.env` dosyasını düzenleyin ve API anahtarınızı ekleyin:
```
GEMINI_API_KEY=your_api_key_here
```

4. **API'yi başlatın (Soil + Weather)**
```bash
cd Backend/API
python main.py
```

## 💻 Kullanım

### Temel Kullanım

Ana chatbot'u çalıştırın:
```bash
python main_chatbot.py
```

**Web Arayüzü**: http://localhost:8001
**API Dokümantasyonu**: http://localhost:8001/docs

### Chatbot Özellikleri

- 🌤️ **Hava Durumu Sorguları**: "Hava durumu nasıl?", "3 günlük tahmin"
- 🧪 **Toprak Analizi**: "Bu koordinattaki toprak nasıl?"
- 🔄 **Birleşik Analiz**: "Hava durumu ve toprak analizi birlikte"
- 📚 **Organik Tarım**: "Organik gübre nasıl yapılır?"

### Test Scripti

Konum servisini test etmek için:
```bash
python deneme.py
```

## 🏗️ Mimari

### Dizin Yapısı

```
LLM/
├── agents/                    # AI Agent modülleri
│   └── research_agents.py    # Araştırma agentı
├── chains/                    # İş akışı zincirleri
│   └── analysis_chain.py     # Analiz zinciri
├── tools/                     # Yardımcı araçlar
│   ├── data_visualitor_tool.py   # Veri görselleştirme
│   ├── rag_tool.py               # RAG bilgi bankası
│   ├── soil_analyzer_tool.py     # Toprak analizi
│   └── weather_tool.py           # Hava durumu
├── env/                       # Virtual environment
├── gps_llm_handler.py        # Ana uygulama
├── deneme.py                 # Test scripti
├── requirements.txt          # Bağımlılıklar
├── .env                      # Ortam değişkenleri
└── README.md                 # Dokümantasyon
```

## 🔧 Modüller

### 🤖 Agents (Agentlar)

#### Research Agent
Toprak araştırmaları için akıllı agent sistemi.

**Özellikler:**
- Çoklu tool entegrasyonu
- Konuşma geçmişi takibi
- Otomatik öneri üretimi
- Verbose logging

**Kullanım:**
```python
from agents.research_agents import ResearchAgent

agent = ResearchAgent(tools=[tool1, tool2], verbose=True)
result = agent.research_soil("toprak pH değerlendirmesi", soil_data)
```

### 🔗 Chains (Zincirler)

#### Analysis Chain
Kapsamlı toprak analizi için iş akışı zinciri.

**İş Akışı:**
1. Veri özetleme
2. Toprak analizi
3. Rapor oluşturma

**Kullanım:**
```python
from chains.analysis_chain import AnalysisChain

chain = AnalysisChain(tools=[visualizer, analyzer])
report = chain.run_analysis(soil_data, analysis_type="comprehensive")
```

### 🛠️ Tools (Araçlar)

#### 1. Data Visualizer Tool
Toprak verilerini görselleştirir ve özetler.

**Metodlar:**
- `create_soil_summary()`: Toprak verisi özeti
- `generate_text_report()`: Metin rapor oluşturma

#### 2. RAG Tool
Organik tarım bilgi bankasından bilgi sorgulama.

**Özellikler:**
- Kaynak takibi
- Yanıt uzunluğu limiti
- Hata yönetimi

#### 3. Soil Analyzer Tool
Toprak özelliklerini analiz eder.

**Fonksiyonlar:**
- pH değerlendirmesi
- Organik karbon analizi
- Ürün uygunluk tespiti

#### 4. Weather Tool
Gerçek hava durumu verilerini sağlar (Open-Meteo API).

**Özellikler:**
- Otomatik konum tespiti (IP tabanlı)
- Manuel koordinat desteği
- Günlük ve saatlik tahminler
- Toprak sıcaklığı ve nem verileri
- Evapotranspirasyon (ET0) değerleri

### 📍 GPS & LLM Handler

Ana uygulama modülü. Konum tespiti ve LLM entegrasyonunu yönetir.

**Konum Yöntemleri:**
1. Windows Konum Servisi (GPS/Wi-Fi)
2. IP tabanlı konum
3. Manuel koordinat girişi

**LLM Entegrasyonu:**
- Google Gemini 2.5 Flash
- Doğal dil toprak analizi
- Türkçe yanıt üretimi

## ⚙️ Konfigürasyon

### API Anahtarları

`.env` dosyasında:
```env
GEMINI_API_KEY=your_gemini_api_key
```

### API Endpoints

**Soil API**: `http://localhost:8000/soiltype/`
**Weather API**: `http://localhost:8000/weather/`
**Chatbot API**: `http://localhost:8001/chat/`

### Tool Konfigürasyonu

Araçları özelleştirmek için:
```python
# RAG tool için maksimum yanıt uzunluğu
rag_tool = RAGTool(rag_chatbot=chatbot, max_response_length=500)

# Weather tool için API URL
weather_tool = WeatherTool(api_base_url="http://localhost:8000")
```

## 🔬 Geliştirme

### Yeni Tool Ekleme

1. `tools/` dizininde yeni bir dosya oluşturun
2. Tool sınıfını tanımlayın:

```python
class YourTool:
    def __init__(self):
        self.name = "Your Tool Name"
        self.description = "Tool açıklaması"
    
    def __call__(self, input_data):
        # Tool mantığı
        return result
```

3. Ana uygulamada kullanın:

```python
from tools.your_tool import YourTool
tool = YourTool()
```

### Yeni Agent Ekleme

`agents/` dizinine yeni agent ekleyin:

```python
class YourAgent:
    def __init__(self, tools=None):
        self.tools = tools or []
        self.conversation_history = []
    
    def execute(self, query):
        # Agent mantığı
        return result
```

### Test

Konum servisini test edin:
```bash
python deneme.py
```

Ana sistemi test edin:
```bash
python gps_llm_handler.py
```

## 📝 Notlar

- API'nin (Soil + Weather) çalışır durumda olması gereklidir
- Windows Konum Servisi için sistem izinleri gerekebilir
- IP tabanlı konum, GPS'e göre daha az hassastır
- RAG sistemi için bilgi bankası yüklenmiş olmalıdır
- Weather API gerçek veri sağlar (Open-Meteo)

## 🐛 Sorun Giderme

### API Bağlantı Hatası
```
Çözüm: API'nin çalıştığından emin olun
cd Backend/API && python main.py
```

### Windows Konum Servisi Hatası
```
Çözüm: Sistem ayarlarından konum iznini etkinleştirin
Ayarlar > Gizlilik > Konum
```

### LLM API Hatası
```
Çözüm: .env dosyasındaki API anahtarını kontrol edin
GEMINI_API_KEY değerinin doğru olduğundan emin olun
```

---

**Not**: Bu sistem aktif geliştirme aşamasındadır. Özellikler ve API'ler değişebilir.