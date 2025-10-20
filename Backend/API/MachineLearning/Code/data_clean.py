# ============================================================
# 🧹 Crop Recommendation — Data Cleaning Script (Final)
# ============================================================

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import os

# ---------- 1️⃣ Veri Yükleme ----------
FILE_PATH = r"C:\Users\ATIF\Downloads\Crop_recommendation.csv"

# 🔹 Noktalı virgülle ayrılmış dosya
df = pd.read_csv(FILE_PATH, sep=';')

print("✅ Veri yüklendi:", df.shape)
print("🧾 Sütunlar:", df.columns.tolist())

# ---------- 2️⃣ Sütun İsimlerini Standartlaştır ----------
df.columns = [col.strip().lower() for col in df.columns]
print("\n🧩 Yeni sütun isimleri:", df.columns.tolist())

# ---------- 3️⃣ Eksik Değer Kontrolü ----------
print("\n🔎 Eksik Değer Kontrolü:")
print(df.isnull().sum())

# ---------- 4️⃣ Sayısal Dönüşüm ----------
# Sayısal sütunları belirle
numeric_cols = [c for c in df.columns if c != 'label']

for col in numeric_cols:
    # Nokta veya virgül içeren sayıları düzelt
    df[col] = (
        df[col]
        .astype(str)
        .str.replace('.', '', regex=False)   # Binlik ayırıcı noktaları kaldır
        .str.replace(',', '.', regex=False)  # Virgülü ondalığa çevir
    )
    df[col] = pd.to_numeric(df[col], errors='coerce')

print("\n📊 Veri tipleri (dönüşüm sonrası):")
print(df.dtypes)

# ---------- 5️⃣ Aykırı Değer Analizi ----------
print("\n⚠️ Aykırı Değer (Outlier) Analizi:")
for col in numeric_cols:
    z_scores = np.abs(stats.zscore(df[col]))
    outliers = (z_scores > 3).sum()
    print(f"{col}: {outliers} potansiyel aykırı değer")

# (İstersen outlier temizliği yapabilirsin ama biz bu projede koruduk)
# df = df[(np.abs(stats.zscore(df[numeric_cols])) < 3).all(axis=1)]

# ---------- 6️⃣ Hedef Değişken Kontrolü ----------
if 'label' not in df.columns:
    raise KeyError("❌ 'label' sütunu bulunamadı! Sütun adlarını kontrol et.")

print("\n🌾 Hedef sınıflar (ürünler):")
print(df['label'].value_counts())

# ---------- 7️⃣ Veri Tipi Dönüşümü ----------
df['label'] = df['label'].astype('category')

# ---------- 8️⃣ Korelasyon Analizi ----------
corr = df[numeric_cols].corr()
plt.figure(figsize=(8,6))
sns.heatmap(corr, annot=True, cmap="YlGnBu")
plt.title("📈 Korelasyon Matrisi — Sayısal Özellikler")
plt.show()

# ---------- 9️⃣ Temiz Veriyi Kaydet ----------
CLEAN_PATH = r"C:\Users\ATIF\Downloads\Crop_recommendation_cleaned.csv"
df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")

print(f"\n💾 Temiz veri kaydedildi: {CLEAN_PATH}")
print(f"📏 Yeni boyut: {df.shape}")
