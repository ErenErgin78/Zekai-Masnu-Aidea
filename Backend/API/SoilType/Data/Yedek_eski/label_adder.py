import pandas as pd
import numpy as np

def main():
    # Dosyaları yükle
    cleaned_df = pd.read_csv('birlesik_veri.csv')
    tarim_df = pd.read_excel('tarım.xlsx', sheet_name='Alfabetik')
    
    # Şehir isimlerini standartlaştır
    cleaned_df['city'] = cleaned_df['city'].str.strip().str.title()
    tarim_df['city'] = tarim_df['city'].str.strip().str.title()
    
    # Bitki verilerini hazırla
    plant_data = {}
    
    for idx, row in tarim_df.iterrows():
        city = row['city']
        plants = []
        
        # Tüm bitki sütunlarını kontrol et
        for col in ['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                plants.append(str(row[col]).strip())
        
        if plants:  # Eğer bitki listesi boş değilse
            plant_data[city] = plants
    
    # Her şehir için sayaç
    counters = {city: 0 for city in plant_data.keys()}
    
    # Bitki atama fonksiyonu
    def get_next_plant(city_name):
        city_name = city_name.strip().title()
        if city_name in plant_data:
            plants = plant_data[city_name]
            if plants:
                current_index = counters[city_name]
                selected_plant = plants[current_index % len(plants)]
                counters[city_name] = current_index + 1
                return selected_plant
        return np.nan
    
    # Bitki sütununu ekle
    cleaned_df['plant'] = cleaned_df['city'].apply(get_next_plant)
    
    # Sonucu kaydet
    cleaned_df.to_csv('cleaned_with_plants.csv', index=False, encoding='utf-8-sig')
    
    # İstatistikleri yazdır
    print("İşlem tamamlandı!")
    print(f"Toplam satır: {len(cleaned_df)}")
    print(f"Bitki atanan satır: {cleaned_df['plant'].notna().sum()}")
    print(f"Eşleşen şehir sayısı: {len(plant_data)}")
    
    # Örnek göster
    print("\nÖrnek veriler:")
    print(cleaned_df[['city', 'plant']].head(15))

if __name__ == "__main__":
    main()