# 🌾 Machine Learning (Ürün Önerisi)

Bu klasör, toprak ve iklim verilerini birleştirerek “bu bölgede hangi ürünler yetişir?” sorusuna yanıt üreten makine öğrenmesi bileşenlerini içerir.

## 🚀 Ne Yapar?
- SoilType API’den toprak özelliklerini alır, iklim özetleriyle birleştirir.
- ML modeli, bu özelliklere göre en uygun ürünleri önerir.
- LLM (chatbot) bu servisi otomatik kullanır; kullanıcıdan manuel koordinat istemez (otomatik konum).

## 🗃️ Veri (Data/final5.csv)
Bu dosya baştan hazırlanmıştır ve üç ana kaynağın birleştirilmiş halidir:
- Şehirlere göre hava durumu özetleri
- SoilType API’den şehirlere göre toprak verileri
- “Hangi şehirde en çok ne yetişiyor” bilgisi

Bu birleşik ve temiz tablo, modelin beslendiği temel veridir.

## 🧩 Veriyi Birleştirme Süreci (Özet)
- `Code/merger.py`: Farklı kaynaklardan gelen şehir bazlı kayıtların tek tabloda birleştirilmesi
- `Code/filler.py`: Eksik değerlerin güvenli biçimde doldurulması (mantıklı varsayılanlar/özetler)
- `Code/labeler.py` ve `Code/binary_labeler.py`: “Hangi şehirde hangi ürün yetişiyor” bilgisinden çok etiketli hedeflerin hazırlanması
- `Code/corr_deleter.py`: Çok yüksek korelasyonlu alanların temizlenmesi; ayrıca ölçekleme ve encoding akışı

Sonuç: `Data/final5.csv` — modelin doğrudan tüketebileceği, temiz ve uyumlu bir tablo.

## 🔬 Modelleme ve Arayış (Code/ml_analysis.py)
- GridSearch ve hiperparametre ayarlaması yapıldı (çok etiketli problem için uygun kurguyla).
- Denenen yaklaşımlar arasında şunlar yer aldı: RandomForest, XGBoost, ExtraTrees, GradientBoosting, SVM, Logistic Regression, KNN, DecisionTree.
- `Data/multi_label_report.txt` dosyasında karşılaştırmalı çıktı/özet skorlar bulunur.

### Neden RandomForest?
- Çok etiketli çıktı yapısında istikrarlı performans (geniş sınıf kümesi ve dengesiz dağılımlarda dayanıklı).
- Özellik sayısı görece yüksek olduğunda dahi aşırı uyum riskini iyi yönetir.
- Hızlı tahmin ve kolay bakım; üretim ortamında güvenilirlik.

> Not: Kod ve raporda görülen diğer iyi modeller (ör. XGBoost, ExtraTrees) yakın sonuçlar vermiştir; ancak genellenebilirlik, sadelik ve bakım maliyeti kriterleri ile RandomForest tercih edilmiştir.

## 🧠 Çalışma Zamanı (API)
- Servis: `ml_api.py`
- Router: `/ml`
- Uçlar:
  - `GET /ml/health`: Servis ve model durumu
  - `POST /ml/analyze`: Ürün önerisi (LLM tarafından otomatik çağrılır)

Çalışma prensibi:
- SoilType verisi arka planda otomatik istenir.
- İklim özellikleri veri setindeki özetlerle tamamlanır.
- Model kullanılamazsa güvenli kural tabanlı öneri çalışır.

## 🤖 LLM Entegrasyonu
- LLM, “burada hangi bitki yetişir?” gibi sorularda ML aracını otomatik çağırır.
- Konum alma her zaman otomatik yapılır (manuel koordinat yoktur).
- Yanıtlar kullanıcı dostudur: “Makine öğrenmesi modeli, toprak ve iklim verilerine göre şu bitkileri önerdi …”.

## 📁 Klasör Yapısı
```
MachineLearning/
├── ml_api.py                 # API router (ML analiz ucu)
├── test_ml_api.py            # Canlı entegrasyon testi (mock yok)
├── Data/
│   ├── final5.csv            # Model beslemesi için birleşik veri
│   └── multi_label_report.txt# Eğitim/analiz kısa sonuçlar
├── Model/
│   └── model.pkl             # Eğitilmiş model (ve meta)
└── Code/
    ├── ml_analysis.py        # GridSearch ve hiperparametre ayarları
    ├── corr_deleter.py       # Korelasyon temizleme + ölçekleme/encoding akışı
    ├── merger.py, filler.py  # Veri birleştirme ve doldurma yardımcıları
    └── ...                   # Etiketleme vb. scriptler
```

## 🧾 İnceleme Özeti
- Boyut: 1564 satır × 75 sütun
- Bellek kullanımı (yaklaşık): 938,532 bayt
- Null sayıları: tüm sütunlarda 0 (eksik değer yok)
- Sayısal özet (örnek):
  - wrb4_code ortalaması ≈ 10.33 (std ≈ 5.17)
  - basic_organic_carbon ortalaması ≈ 1.75
  - texture_clay ≈ 23.55, texture_sand ≈ 38.10
  - chemical_base_saturation ≈ 84.27
- Etiket sütunları: 38 ürün etiketi (ör. label_Buğday, label_Pamuk, label_Zeytin …)