import pandas as pd
import numpy as np
import re
import os

def standardize_city_name(city_name):
    """
    Şehir adlarını küçük harfe çevirir, Türkçe karakterleri standartlaştırır 
    ve boşlukları temizler (Eşleştirme için kritik).
    """
    if pd.isna(city_name):
        return city_name
        
    name = str(city_name).strip().lower()
    
    # Türkçe karakterleri standardize et
    name = name.replace('ç', 'c')
    name = name.replace('ğ', 'g')
    name = name.replace('ı', 'i')
    name = name.replace('ö', 'o')
    name = name.replace('ş', 's')
    name = name.replace('ü', 'u')
    name = name.replace('i̇', 'i').lower() 
    
    return name

def assign_cyclic_crops_final(final3_file_path, crops_file_path='city.csv', output_file_path='final3_labeled_cyclic_FINAL.csv'):
    """
    final3.csv ve city.csv dosyalarını birleştirir, aynı şehirlere ürünleri 
    döngüsel olarak (sırayla) atar.
    """
    print("--- Veri Yükleme Başladı ---")
    
    # 1. Şehir/Ürün verilerini yükle
    try:
        df_crops = pd.read_csv(crops_file_path) 
    except FileNotFoundError:
        print(f"HATA: Ürünler dosyası bulunamadı: '{crops_file_path}'.")
        return

    # 2. Ana veri (final3) dosyasını yükle
    try:
        df_final3 = pd.read_csv(final3_file_path)
        # Sütun adını uyumlu hale getir
        df_final3.rename(columns={'city': 'City'}, inplace=True, errors='ignore') 
    except FileNotFoundError:
        print(f"HATA: Ana veri dosyası bulunamadı: '{final3_file_path}'.")
        return
    
    # Sütun adlarının varlığını kontrol et
    if 'City' not in df_final3.columns:
        print("HATA: 'final3.csv' dosyasında 'city' veya 'City' sütunu bulunamadı.")
        return
        
    # 3. Şehir İsimlerini Standartlaştır (Eşleştirme için ZORUNLU ADIM)
    df_final3['City_Std'] = df_final3['City'].apply(standardize_city_name)
    df_crops['City_Std'] = df_crops['City'].apply(standardize_city_name)
    
    print("Şehir isimleri standartlaştırıldı.")
    
    # 4. Ürün listesi sözlüğünü hazırla
    # TopCrops sütunundaki metni liste formatına çevir
    df_crops['Crops_List'] = df_crops['TopCrops'].str.split(';').apply(lambda x: [c.strip() for c in x])
    
    # Standartlaştırılmış şehir adlarını kullanarak sözlük oluştur
    crop_dict = df_crops.set_index('City_Std')['Crops_List'].to_dict()

    # 5. Döngüsel Atama Hazırlığı
    assigned_labels = [] # Yeni etiketleri tutacak liste
    # Hangi şehrin hangi üründe kaldığını takip eden sözlük
    city_crop_index = {city_std: 0 for city_std in crop_dict.keys()}

    print("\nDöngüsel Etiket Atama Başladı...")

    # 6. Atama İşlemi
    for index, row in df_final3.iterrows():
        current_city_std = row['City_Std']
        assigned_crop = np.nan # Eşleşme olmazsa NaN kalır
        
        if current_city_std in crop_dict:
            crops = crop_dict[current_city_std]
            num_crops = len(crops)
            
            # Şehir için mevcut indeksi al
            current_index = city_crop_index[current_city_std]
            
            # Ürünü ata
            assigned_crop = crops[current_index]
            
            # İndeksi döngüsel olarak ilerlet
            city_crop_index[current_city_std] = (current_index + 1) % num_crops
            
        assigned_labels.append(assigned_crop)

    print("Döngüsel Etiket Atama Tamamlandı.")

    # 7. Listeyi DataFrame'e ekle ve Kaydet
    df_final3['label'] = assigned_labels 
    
    # Geçici standartlaştırma sütununu sil
    df_final3.drop(columns=['City_Std'], inplace=True)
    
    # Sonucu kaydet
    df_final3.to_csv(output_file_path, index=False, encoding='utf-8-sig')

    print(f"\n--- İşlem Tamamlandı ---")
    print(f"Yeni 'label' sütunu eklenmiş dosya şuraya kaydedildi: '{output_file_path}'")
    print(f"Toplam etiketlenemeyen (NaN) satır sayısı: {df_final3['label'].isnull().sum()}")

# --- KODU ÇALIŞTIRMA ---
if __name__ == "__main__":
    # Lütfen bu iki dosyanın (final3.csv ve city.csv) aynı klasörde olduğundan emin olun.
    assign_cyclic_crops_final(final3_file_path='final3.csv', crops_file_path='city.csv')