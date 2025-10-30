import pandas as pd
import numpy as np
import re

def standardize_city_name(city_name):
    """
    Şehir adlarını küçük harfe çevirir, Türkçe karakterleri standartlaştırır 
    ve boşlukları temizler.
    """
    if pd.isna(city_name):
        return city_name
        
    name = str(city_name).strip().lower()
    
    # Türkçe karakterleri standardize et
    # Bu adım, iki veri setinde de tutarsızlıkları önler
    name = name.replace('ç', 'c')
    name = name.replace('ğ', 'g')
    name = name.replace('ı', 'i')
    name = name.replace('ö', 'o')
    name = name.replace('ş', 's')
    name = name.replace('ü', 'u')
    # Büyük 'I' sorununu engellemek için tekrar küçük harfe çevirme
    name = name.replace('i̇', 'i').lower() 
    
    return name

def assign_cyclic_crops_fixed(final3_file_path, output_file_path='final3_labeled_cyclic_FIXED.csv'):
    """
    İki CSV dosyasını birleştirir ve final3'teki aynı şehirler için
    ürünleri döngüsel olarak (sırayla) atar. (Şehir Eşleşme Hataları Giderildi)
    """
    print("--- Veri Yükleme ve Standartlaştırma Başladı ---")
    
    # --------------------------------------------------------------------------
    # 1. Şehir ve Ürün verilerini yükle (Önceki çıktıdaki metinsel veriyi kullanıyoruz)
    # --------------------------------------------------------------------------
    data_crops = """City,TopCrops
Adana,Pamuk; Mısır; Narenciye
Adıyaman,Pamuk; Buğday; Tütün
Afyonkarahisar,Haşhaş; Patates; Şeker Pancarı
Ağrı,Buğday; Arpa; Patates
Aksaray,Buğday; Arpa; Şeker Pancarı
Amasya,Elma; Kiraz; Şeftali
Ankara,Buğday; Arpa; Şeker Pancarı
Çanakkale,Buğday; Zeytin; Sebze # Örnek çıktıdaki şehirleri de ekleyelim
Edirne,Pirinç; Buğday; Ayçiçeği
İzmir,Zeytin; Üzüm; Pamuk
""" 
    from io import StringIO
    df_crops = pd.read_csv(StringIO(data_crops)) 

    # 2. Toprak/İklim verilerini yükle
    try:
        df_final3 = pd.read_csv(final3_file_path)
        # Sütun adı uyumsuzluğunu gidermek için 'city' -> 'City' yap
        df_final3.rename(columns={'city': 'City'}, inplace=True) 
    except FileNotFoundError:
        print(f"HATA: Dosya bulunamadı: '{final3_file_path}'")
        return
    
    # 3. Şehir İsimlerini Standartlaştır (Kritik Adım!)
    df_final3['City_Std'] = df_final3['City'].apply(standardize_city_name)
    df_crops['City_Std'] = df_crops['City'].apply(standardize_city_name)

    print("Şehir isimleri standartlaştırıldı.")
    
    # 4. Ürün listesini hazırlama ve Sözlük oluşturma
    df_crops['Crops_List'] = df_crops['TopCrops'].str.split(';').apply(lambda x: [c.strip() for c in x])
    
    # Standartlaştırılmış şehir adlarını kullanarak sözlük oluştur
    crop_dict = df_crops.set_index('City_Std')['Crops_List'].to_dict()

    # 5. Döngüsel Atama İçin Hazırlık
    assigned_labels = [] 
    city_crop_index = {city_std: 0 for city_std in crop_dict.keys()}

    print("\nDöngüsel Etiket Atama Başladı...")

    # 6. Atama İşlemi
    for index, row in df_final3.iterrows():
        current_city_std = row['City_Std']
        assigned_crop = np.nan
        
        if current_city_std in crop_dict:
            crops = crop_dict[current_city_std]
            num_crops = len(crops)
            
            current_index = city_crop_index[current_city_std]
            
            assigned_crop = crops[current_index]
            
            # İndeksi bir sonraki ürüne kaydır (döngüsel olarak)
            city_crop_index[current_city_std] = (current_index + 1) % num_crops
            
        assigned_labels.append(assigned_crop)

    print("Döngüsel Etiket Atama Tamamlandı.")

    # 7. Listeyi DataFrame'e ekle ve Kaydet
    df_final3['label'] = assigned_labels 
    
    # Standartlaştırma sütununu silebiliriz
    df_final3.drop(columns=['City_Std'], inplace=True)
    
    df_final3.to_csv(output_file_path, index=False, encoding='utf-8-sig')

    print("\n--- İşlem Sonucu ---")
    print(f"Yeni 'label' sütunu eklenmiş dosya şuraya kaydedildi: '{output_file_path}'")
    print("İlk 10 satır:")
    print(df_final3[['City', 'label']].head(10))

# --- ÇALIŞTIRMA ---
# NOT: Lütfen 'final3.csv' dosyanızın aynı dizinde olduğundan emin olun.
assign_cyclic_crops_fixed(final3_file_path='final3.csv')