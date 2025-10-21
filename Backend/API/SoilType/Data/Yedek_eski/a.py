import pandas as pd
import unicodedata

# Türkçe karakterleri standartlaştırmak için fonksiyon
def normalize_city_name(name):
    if pd.isna(name):
        return name
    # Büyük harfe çevir ve boşlukları temizle
    name = str(name).strip().upper()
    # Türkçe karakterleri İngilizce karşılıklarına çevir
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name

# CSV dosyalarını yükle
cleaned_df = pd.read_csv('soil.csv')
iklim_df = pd.read_csv('iklim.csv')

# İklim dosyasındaki city sütun adını düzelt
iklim_df = iklim_df.rename(columns={'ity': 'city'})

# Şehir isimlerini normalleştir
cleaned_df['city_normalized'] = cleaned_df['city'].apply(normalize_city_name)
iklim_df['city_normalized'] = iklim_df['city'].apply(normalize_city_name)

# İki DataFrame'i normalleştirilmiş şehir isimlerine göre birleştir
merged_df = pd.merge(cleaned_df, iklim_df, on='city_normalized', how='left', suffixes=('', '_iklim'))

# Orijinal şehir isimlerini koru (cleaned'den alınan)
merged_df = merged_df.drop(['city_normalized', 'city_iklim'], axis=1, errors='ignore')

# Eşleşmeyen şehirleri kontrol et
if 'Ortalama Sıcaklık (°C)_Ocak' in merged_df.columns:
    missing_cities = merged_df[merged_df['Ortalama Sıcaklık (°C)_Ocak'].isna()]['city'].unique()
else:
    # Eğer hiç eşleşme olmazsa
    missing_cities = merged_df['city'].unique()
    
print(f"İklim verisi bulunamayan şehirler: {list(missing_cities)}")
print(f"Toplam {len(missing_cities)} şehrin iklim verisi bulunamadı")

# Sonuçları kaydet
merged_df.to_csv('birlesik_veri.csv', index=False, encoding='utf-8-sig')

print("Birleştirme işlemi tamamlandı. 'birlesik_veri.csv' dosyası oluşturuldu.")