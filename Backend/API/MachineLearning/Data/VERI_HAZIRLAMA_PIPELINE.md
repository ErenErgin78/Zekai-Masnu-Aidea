# Veri Hazırlama Pipeline'ı - Aşama Aşama Açıklama

Bu doküman, makine öğrenmesi modeli için veri hazırlama sürecinde kullanılan tüm script'lerin ne yaptığını ve hangi sırayla çalıştığını açıklar.

## 📊 Genel Veri Akışı

```
final.csv → filler.py → final2.csv → corr_deleter.py → final3.csv → 
label_deleter.py → labeler.py → final4.csv → binary_labeler.py → 
final5.csv → ml_analysis.py → Model + Raporlar
```

---

## 🔄 AŞAMA 1: Eksik Veri Doldurma (`filler.py`)

**Giriş:** `final.csv`  
**Çıkış:** `final2.csv`  
**Amaç:** Eksik hava durumu verilerini coğrafi komşuluk kullanarak doldurma

### Yapılan İşlemler:

1. **Hava Durumu Sütunlarını Belirleme**
   - `Ortalama Sıcaklık (°C)`
   - `Ortalama En Yüksek Sıcaklık (°C)`
   - `Ortalama En Düşük Sıcaklık (°C)`
   - `Ortalama Güneşlenme Süresi (saat)`
   - `Ortalama Yağışlı Gün Sayısı`
   - `Aylık Toplam Yağış Miktarı Ortalaması (mm)`

2. **Eksik Veri Tespiti**
   - Hava durumu sütunlarında eksik değer bulunan satırlar belirlenir
   - `latitude`, `longitude`, `city` bilgisi eksik olan satırlar atlanır

3. **Coğrafi Komşuluk Analizi**
   - BallTree kullanarak Haversine mesafesi ile en yakın komşular bulunur
   - Aynı şehirden veri alınmaz (farklı şehir komşusu seçilir)
   - En yakın 10 komşu kontrol edilir, ilk farklı şehirli komşunun verisi kopyalanır

4. **Sonuç**
   - Eksik veriler doldurulmuş `final2.csv` oluşturulur
   - İstatistikler: Kaç satır dolduruldu, kaç satır doldurulamadı

---

## 🔄 AŞAMA 2: Yüksek Korelasyonlu Sütunları Silme (`corr_deleter.py`)

**Giriş:** `final2.csv`  
**Çıkış:** `final2_selectively_cleaned.csv` (muhtemelen `final3.csv`'ye dönüştürülüyor)  
**Amaç:** Gereksiz bilgi taşıyan yüksek korelasyonlu özellikleri temizleme

### Yapılan İşlemler:

1. **Korelasyon Matrisi Hesaplama**
   - Sadece sayısal sütunlar seçilir
   - Mutlak korelasyon matrisi hesaplanır
   - Üst üçgen matris kullanılarak çiftler tespit edilir

2. **Stratejik Silme Algoritması**
   - Eşik değer: **0.85** (varsayılan)
   - Her yüksek korelasyonlu çift için hangi sütunun silineceğine karar verilir
   - **Strateji:** En çok yüksek korelasyonlu çiftte yer alan sütun silinir
   - Bu, en "gereksiz" (redundant) bilgiyi taşıyan sütunu tespit eder

3. **Toplu Silme**
   - Silme işlemi tamamlanana kadar döngü devam eder
   - Her iterasyonda en problemli sütun silinir
   - O sütunla ilgili tüm çiftler listeden çıkarılır

4. **Sonuç**
   - Temizlenmiş veri seti oluşturulur
   - Silinen sütunlar listesi raporlanır
   - Boyut azaltması gerçekleşir (örnek: 771KB → 298KB)

---

## 🔄 AŞAMA 3: Gereksiz Sütun Silme (`label_deleter.py`)

**Giriş:** `final3.csv`  
**Çıkış:** `final3.csv` (aynı dosya, güncellenmiş)  
**Amaç:** Kullanılmayan `plant` sütununu silme

### Yapılan İşlemler:

1. **Sütun Silme**
   - `plant` sütunu veri setinden çıkarılır
   - Basit bir temizlik işlemi

2. **Sonuç**
   - Daha temiz veri seti elde edilir
   - Gereksiz sütunlar kaldırılır

---

## 🔄 AŞAMA 4: Şehir-Ürün Eşleştirme ve Etiket Atama (`labeler.py`)

**Giriş:** `final3.csv`, `city.csv`  
**Çıkış:** `final3_labeled_cyclic_FINAL.csv` (muhtemelen `final4.csv`'ye dönüştürülüyor)  
**Amaç:** Her şehre, o şehirde yetişen ürünlerden birini döngüsel olarak etiket olarak atama

### Yapılan İşlemler:

1. **Şehir İsimlerini Standartlaştırma**
   - Türkçe karakterler standartlaştırılır (ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u)
   - Küçük harfe çevrilir
   - Boşluklar temizlenir
   - Bu, eşleştirme hatalarını önler

2. **Şehir-Ürün Eşleştirmesi**
   - `city.csv` dosyasından şehir-ürün eşleştirmesi yüklenir
   - Her şehir için yetişen ürünler listesi oluşturulur
   - Örnek: Adana → [Pamuk, Mısır, Narenciye]

3. **Döngüsel Etiket Atama**
   - Aynı şehirdeki farklı satırlar için farklı ürünler atanır
   - Her şehir için bir sayaç tutulur
   - İlk satır → ilk ürün, ikinci satır → ikinci ürün, ...
   - Ürün listesi bitince başa döner (döngüsel)

4. **Örnek:**
   ```
   Adana (satır 1) → Pamuk
   Adana (satır 2) → Mısır
   Adana (satır 3) → Narenciye
   Adana (satır 4) → Pamuk (döngü başa döndü)
   ```

5. **Sonuç**
   - Her satıra bir `label` sütunu eklenir
   - Tek-label (single-label) veri seti oluşturulur

---

## 🔄 AŞAMA 5: Multi-Label Veri Seti Hazırlama (`binary_labeler.py`)

**Giriş:** `final4.csv`, `city.csv`  
**Çıkış:** `final5.csv`  
**Amaç:** Tek-label veri setini multi-label format'a çevirme (Binary Relevance için)

### Yapılan İşlemler:

1. **Label Sütununu Silme**
   - Tek-label `label` sütunu kaldırılır
   - Özellik sütunları korunur

2. **Koordinat ve Şehir Sütunlarını Temizleme**
   - `longitude`, `latitude`, `City` sütunları çıkarılır
   - Sadece özellik sütunları kalır

3. **Kategorik Sütunları Sayısal Değerlere Dönüştürme**
   - LabelEncoder kullanılarak kategorik sütunlar sayısal hale getirilir

4. **Multi-Label Matrix Oluşturma**
   - Tüm şehirlerden tüm ürünler toplanır (benzersiz liste)
   - Her satır için bir binary vektör oluşturulur:
     - Şehirde yetişen ürün → 1
     - Şehirde yetişmeyen ürün → 0
   - Örnek: Adana için → [Pamuk:1, Mısır:1, Narenciye:1, Buğday:0, ...]

5. **Binary Label Sütunları Ekleme**
   - Her ürün için `label_{ürün_adi}` sütunu eklenir
   - Örnek: `label_Pamuk`, `label_Mısır`, `label_Buğday`, ...

6. **Rapor Oluşturma**
   - `final5_summary.txt`: Veri seti özeti, ürün listesi, label dağılımı
   - `final5_info.json`: Teknik detaylar (JSON formatında)

7. **Sonuç**
   - Multi-label veri seti hazırlanır
   - Her satır birden fazla ürün için etiket içerir
   - Binary Relevance algoritması için uygun format

---

## 🔄 AŞAMA 6: Makine Öğrenmesi Modeli Eğitimi (`ml_analysis.py`)

**Giriş:** `final5.csv`  
**Çıkış:** 
- `Model/model2.pkl` (eğitilmiş model)
- `Data/final_report.txt` (detaylı rapor)
- `Grafikler/*.png` (performans grafikleri)

**Amaç:** Multi-label classification modeli eğitme ve değerlendirme

### Yapılan İşlemler:

1. **Veri Hazırlama**
   - Label sütunları (`label_*`) ayrılır
   - Özellik sütunları hazırlanır
   - Tek sınıflı label'lar tespit edilir ve çıkarılır
   - Kategorik sütunlar sayısal değerlere dönüştürülür
   - Eksik değerler ortalama ile doldurulur
   - Sonsuz değerler kontrol edilir ve düzeltilir

2. **Train-Test Split**
   - %80 eğitim, %20 test
   - Random state: 42 (reproducibility için)

3. **Özellik Ölçeklendirme**
   - StandardScaler ile normalizasyon
   - Eğitim setinden öğrenilen parametreler test setine uygulanır

4. **Model Tarama ve GridSearch**
   - **8 farklı algoritma test edilir:**
     - RandomForest
     - LogisticRegression
     - SVM
     - XGBoost
     - ExtraTrees
     - GradientBoosting
     - KNN
     - DecisionTree
   - Her model için GridSearchCV ile hiperparametre optimizasyonu
   - 3-fold cross-validation
   - F1-Macro skoruna göre en iyi model seçilir

5. **Model Değerlendirme**
   - **Metrikler:**
     - Accuracy
     - F1-Micro
     - F1-Macro
     - Hamming Loss
     - Jaccard Score
   - **Ürün bazlı performans:**
     - Her ürün için Precision, Recall, F1-Score
     - True Positives, False Positives, False Negatives, True Negatives

6. **Rapor Oluşturma**
   - Veri hazırlama özeti
   - Eğitim/doğrulama istatistikleri
   - Model karşılaştırması
   - Ürün bazlı performans detayları
   - GridSearch en iyi parametreleri

7. **Görselleştirme**
   - Model karşılaştırma grafikleri (F1-Macro, Accuracy)
   - Ürün bazlı F1-Score grafiği
   - Ürün bazlı Precision/Recall grafiği

8. **Model Kaydetme**
   - En iyi model `Model/model2.pkl` olarak kaydedilir
   - Model, scaler ve metadata birlikte kaydedilir

---

## 📋 Özet: Veri Dönüşüm Süreci

| Aşama | Giriş Dosyası | Çıkış Dosyası | Boyut Değişimi | Ana İşlem |
|-------|--------------|---------------|----------------|-----------|
| 1 | `final.csv` | `final2.csv` | ~758KB → ~771KB | Eksik veri doldurma |
| 2 | `final2.csv` | `final3.csv` | ~771KB → ~298KB | Yüksek korelasyonlu sütun silme |
| 3 | `final3.csv` | `final3.csv` | Değişmez | `plant` sütunu silme |
| 4 | `final3.csv` | `final4.csv` | ~298KB → ~310KB | Tek-label etiket atama |
| 5 | `final4.csv` | `final5.csv` | ~310KB → ~386KB | Multi-label format'a çevirme |
| 6 | `final5.csv` | Model + Raporlar | - | ML modeli eğitimi |

---

## 🎯 Her Aşamanın Amacı

1. **filler.py:** Veri kalitesini artırma (eksik veri sorunu giderme)
2. **corr_deleter.py:** Özellik seçimi (gereksiz özellikleri çıkarma, boyut azaltma)
3. **label_deleter.py:** Veri temizliği (kullanılmayan sütunları kaldırma)
4. **labeler.py:** Etiket oluşturma (hedef değişkeni oluşturma)
5. **binary_labeler.py:** Format dönüşümü (multi-label problem için uygun format)
6. **ml_analysis.py:** Model geliştirme (eğitim, değerlendirme, raporlama)

---

## ⚠️ Önemli Notlar

- **Sıralama kritiktir:** Script'ler belirli bir sırayla çalıştırılmalıdır
- **Ara dosyalar:** Her aşama bir sonraki için gerekli formatı sağlar
- **Veri kaybı:** Korelasyon silme ve temizleme işlemleri boyutu azaltır (gerekli)
- **Multi-label:** Final aşamada tek-label → multi-label dönüşümü yapılır
- **Reproducibility:** Random state'ler sabit tutularak sonuçlar tekrarlanabilir hale getirilir

