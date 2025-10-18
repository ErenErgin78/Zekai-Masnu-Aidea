# ============================================================
# 🌾 Crop & Soil — Pre-Model Pipeline (Cleaning + EDA + Split + Scaling)
# ============================================================
# Bu dosya, model kurmadan ÖNCE yapılması gereken tüm adımları içerir.
# - Dosyayı doğru ayraç ve encoding ile okur
# - Tip/isim düzeltmeleri + eksik değer doldurma
# - Mantıksal outlier temizliği
# - Hedef sütunu (Crop_Type) oluşturma
# - Sadece gerekli kategorikler için One-Hot Encoding
# - Keşifsel Veri Analizi (EDA) görselleri
# - Train-Test split + sadece eğitim setine fit edilen scaler
# - Temiz veriyi diske kaydetme
# ============================================================

# ---------- 0) IMPORTS ----------
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ---------- 1) VERİYİ YÜKLE ----------
# Orijinal ham dosya (Kaggle.csv) ; ile ayrılmış
RAW_PATH = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea\Backend\API\MachineLearning\Data\Kaggle.csv"
CLEAN_PATH = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea\Backend\API\MachineLearning\Data\Crop_Soil_Final.csv"

df = pd.read_csv(RAW_PATH, encoding="ISO-8859-1", sep=";")
print(f"✅ Ham veri yüklendi: {df.shape}")

# ---------- 2) TİP DÜZELTMELERİ + EKSİKLER ----------
# Not: Kaggle.csv'de 'Temparature' yanlış yazımlı. Düzeltip sayıya çeviriyoruz.
if "Temparature" in df.columns:
    df["Temparature"] = (
        df["Temparature"].astype(str).str.replace(",", ".", regex=False)
    )
    df["Temparature"] = pd.to_numeric(df["Temparature"], errors="coerce")
    df.rename(columns={"Temparature": "Temperature"}, inplace=True)

# Moisture da metin gelebilir → sayıya çevir
if "Moisture" in df.columns:
    df["Moisture"] = pd.to_numeric(
        df["Moisture"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

# Basit boşluk doldurma (median)
for col in ["Temperature", "Moisture"]:
    if col in df.columns:
        df[col].fillna(df[col].median(), inplace=True)

print("🔧 Tip/eksik temizliği tamamlandı.")

# ---------- 3) AYKIRI DEĞER TEMİZLİĞİ ----------
# Mantıksal sınırlar: Temperature [0, 60], Humidity & Moisture [0, 100]
bounds = []
if "Temperature" in df.columns:
    bounds.append((df["Temperature"] >= 0) & (df["Temperature"] <= 60))
if "Humidity" in df.columns:
    bounds.append((df["Humidity"] >= 0) & (df["Humidity"] <= 100))
if "Moisture" in df.columns:
    bounds.append((df["Moisture"] >= 0) & (df["Moisture"] <= 100))

if bounds:
    before = len(df)
    mask = np.logical_and.reduce(bounds)
    df = df[mask].copy()
    after = len(df)
    print(f"🧹 Outlier filtresi uygulandı: {before} → {after}")

# Örnek: Potassium için yüzde 5–95 kırpma (hafif, güvenli)
if "Potassium" in df.columns:
    low, high = df["Potassium"].quantile([0.05, 0.95])
    df["Potassium"] = df["Potassium"].clip(low, high)

# ---------- 4) HEDEF SÜTUNU OLUŞTUR ----------
# Ham dosyada 'Crop Type' kategorik; doğrudan hedefe kopyalıyoruz.
# (One-hot'tan geri birleştirme yerine daha sade ve tekrarsız.)
if "Crop Type" not in df.columns:
    raise ValueError("Beklenen 'Crop Type' kolonu bulunamadı.")
df["Crop_Type"] = df["Crop Type"].astype(str)

# ---------- 5) ONE-HOT ENCODING (yalnızca özellikler için) ----------
# Sadece özellik tarafındaki kategorikleri kodlayalım:
cat_cols = [c for c in ["Soil Type", "Fertilizer Name"] if c in df.columns]
df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

# Artık eski 'Crop Type' kolonuna ihtiyacımız yok (etiket kopyalandı)
df.drop(columns=["Crop Type"], inplace=True)

print(f"🧱 One-Hot sonrası şekil: {df.shape}")

# ---------- 6) EDA (Keşifsel Analiz) ----------
# (Grafikler Spyder'ın Plots panelinde görünür)
print("\n📈 Tanımlayıcı istatistikler (sayısal):")
print(df.select_dtypes(include=[np.number]).describe().T)

plt.figure(figsize=(10, 4))
sns.countplot(x="Crop_Type", data=df)
plt.title("Crop_Type Dağılımı")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

if "Temperature" in df.columns:
    plt.figure(figsize=(8, 4))
    sns.boxplot(x="Crop_Type", y="Temperature", data=df)
    plt.title("Temperature — Crop_Type bazında dağılım")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

plt.figure(figsize=(9, 7))
sns.heatmap(
    df.select_dtypes(include=[np.number]).corr(),
    cmap="coolwarm",
    annot=False,
)
plt.title("Korelasyon Matrisi (sayısal)")
plt.tight_layout()
plt.show()

# ---------- 7) TRAIN–TEST SPLIT ----------
TARGET_COL = "Crop_Type"
X = df.drop(columns=[TARGET_COL])
y = df[TARGET_COL]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"✂ Split → Train: {X_train.shape}, Test: {X_test.shape}")

# ---------- 8) FEATURE SCALING (yalnızca eğitim setine fit) ----------
num_cols = X_train.select_dtypes(include=[np.number]).columns
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train[num_cols])
X_test_scaled = scaler.transform(X_test[num_cols])

print(f"⚖ Scaling tamam: {len(num_cols)} sayısal sütun ölçeklendi.")

# ---------- 9) TEMİZ DOSYAYI KAYDET ----------
# (Model eğitiminde tekrar kullanmak istersen)
# Not: sep=';' verildi ki okurken yine ; ile okunabilsin.
df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig", sep=";")
print(f"💾 Temiz veri kaydedildi → {CLEAN_PATH}")

# ---------- 10) ÖZET ----------
print("\n✅ ÖN HAZIRLIK TAMAM — modelleme için hazırsın.")
print("Kullanıma hazır objeler: df, X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled")