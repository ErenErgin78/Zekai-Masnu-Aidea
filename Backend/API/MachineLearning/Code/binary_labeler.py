#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Label Veri Seti Hazırlama
final4.csv'den label'ı siler ve Binary Relevance için multi-label veri seti oluşturur
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

def load_city_crops_data():
    """Şehir-ürün verilerini yükler"""
    print("🔄 Şehir-ürün verileri yükleniyor...")
    
    city_crops_path = os.path.join(os.path.dirname(__file__), "Data", "city.csv")
    df_cities = pd.read_csv(city_crops_path)
    
    print(f"✅ {len(df_cities)} şehir verisi yüklendi")
    
    # Şehir-ürün mapping'i oluştur
    city_crops_mapping = {}
    for _, row in df_cities.iterrows():
        city = row['City']
        crops = [crop.strip() for crop in row['TopCrops'].split(';')]
        city_crops_mapping[city] = crops
    
    return city_crops_mapping

def prepare_multi_label_dataset(df, city_crops_mapping):
    """Multi-label veri seti hazırlar"""
    print("🔄 Multi-label veri seti hazırlanıyor...")
    
    # Label sütununu sil
    df_no_label = df.drop('label', axis=1)
    print(f"✅ Label sütunu silindi")
    
    # Koordinat ve şehir sütunlarını çıkar
    columns_to_drop = ['longitude', 'latitude', 'City']
    df_features = df_no_label.drop(columns=columns_to_drop, errors='ignore')
    
    print(f"📊 Özellik sayısı: {df_features.shape[1]}")
    
    # Kategorik sütunları sayısal değerlere dönüştür
    categorical_columns = df_features.select_dtypes(include=['object']).columns
    if len(categorical_columns) > 0:
        print(f"🔄 Kategorik sütunlar işleniyor: {list(categorical_columns)}")
        for col in categorical_columns:
            le = LabelEncoder()
            df_features[col] = le.fit_transform(df_features[col].astype(str))
    
    # Multi-label matrix oluştur
    all_crops = set()
    for crops in city_crops_mapping.values():
        all_crops.update(crops)
    
    all_crops = sorted(list(all_crops))
    print(f"📊 Toplam ürün sayısı: {len(all_crops)}")
    print(f"📊 Ürünler: {', '.join(all_crops[:10])}{'...' if len(all_crops) > 10 else ''}")
    
    # Her satır için multi-label matrix
    multi_label_matrix = []
    for _, row in df.iterrows():
        city = row['City']
        city_crops = city_crops_mapping.get(city, [])
        
        # Bu şehir için hangi ürünler yetişiyor?
        label_vector = [1 if crop in city_crops else 0 for crop in all_crops]
        multi_label_matrix.append(label_vector)
    
    multi_label_matrix = np.array(multi_label_matrix)
    
    print(f"📊 Multi-label matrix boyutu: {multi_label_matrix.shape}")
    print(f"📊 Ortalama ürün sayısı/şehir: {multi_label_matrix.sum(axis=1).mean():.2f}")
    
    # Multi-label sütunlarını DataFrame'e ekle
    for i, crop in enumerate(all_crops):
        df_features[f'label_{crop}'] = multi_label_matrix[:, i]
    
    print(f"📊 Final veri seti boyutu: {df_features.shape}")
    
    return df_features, all_crops

def save_dataset_info(all_crops, df_features):
    """Veri seti bilgilerini kaydeder"""
    print("\n💾 Veri seti bilgileri kaydediliyor...")
    
    # Ürün listesi
    crops_info = {
        'total_crops': len(all_crops),
        'crops': all_crops,
        'dataset_shape': df_features.shape,
        'features': list(df_features.columns),
        'label_columns': [f'label_{crop}' for crop in all_crops]
    }
    
    # JSON olarak kaydet
    info_path = os.path.join(os.path.dirname(__file__), "final5_info.json")
    import json
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(crops_info, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Veri seti bilgileri kaydedildi: {info_path}")
    
    return crops_info

def generate_summary_report(df_features, all_crops, city_crops_mapping):
    """Özet rapor oluşturur"""
    print("\n📝 Özet raporu oluşturuluyor...")
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("MULTI-LABEL VERİ SETİ HAZIRLAMA RAPORU")
    report_lines.append("=" * 80)
    report_lines.append(f"Rapor Tarihi: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Veri seti bilgileri
    report_lines.append("VERİ SETİ BİLGİLERİ")
    report_lines.append("-" * 40)
    report_lines.append(f"Toplam satır: {df_features.shape[0]}")
    report_lines.append(f"Toplam sütun: {df_features.shape[1]}")
    report_lines.append(f"Özellik sayısı: {df_features.shape[1] - len(all_crops)}")
    report_lines.append(f"Label sayısı: {len(all_crops)}")
    report_lines.append("")
    
    # Ürün bilgileri
    report_lines.append("ÜRÜN BİLGİLERİ")
    report_lines.append("-" * 40)
    report_lines.append(f"Toplam ürün sayısı: {len(all_crops)}")
    report_lines.append("Ürünler:")
    for i, crop in enumerate(all_crops, 1):
        report_lines.append(f"  {i:2d}. {crop}")
    report_lines.append("")
    
    # Şehir-ürün dağılımı
    report_lines.append("ŞEHİR-ÜRÜN DAĞILIMI")
    report_lines.append("-" * 40)
    for city, crops in list(city_crops_mapping.items())[:10]:  # İlk 10 şehir
        report_lines.append(f"{city}: {', '.join(crops)}")
    if len(city_crops_mapping) > 10:
        report_lines.append(f"... ve {len(city_crops_mapping) - 10} şehir daha")
    report_lines.append("")
    
    # Label dağılımı
    report_lines.append("LABEL DAĞILIMI")
    report_lines.append("-" * 40)
    label_columns = [f'label_{crop}' for crop in all_crops]
    label_counts = df_features[label_columns].sum().sort_values(ascending=False)
    
    for crop, count in label_counts.items():
        crop_name = crop.replace('label_', '')
        percentage = (count / len(df_features)) * 100
        report_lines.append(f"{crop_name}: {count} şehir ({percentage:.1f}%)")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("RAPOR SONU")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)

def main():
    """Ana fonksiyon"""
    print("🚀 Multi-Label Veri Seti Hazırlama Başlıyor...")
    print("=" * 60)
    
    try:
        # Veri yükle
        df_path = os.path.join(os.path.dirname(__file__), "final4.csv")
        df = pd.read_csv(df_path)
        print(f"✅ final4.csv yüklendi: {df.shape[0]} satır, {df.shape[1]} sütun")
        
        # Şehir-ürün verilerini yükle
        city_crops_mapping = load_city_crops_data()
        
        # Multi-label veri seti hazırla
        df_final, all_crops = prepare_multi_label_dataset(df, city_crops_mapping)
        
        # Veri setini kaydet
        final_path = os.path.join(os.path.dirname(__file__), "final5.csv")
        df_final.to_csv(final_path, index=False, encoding='utf-8')
        print(f"✅ Multi-label veri seti kaydedildi: {final_path}")
        
        # Veri seti bilgilerini kaydet
        crops_info = save_dataset_info(all_crops, df_final)
        
        # Özet raporu oluştur
        report_content = generate_summary_report(df_final, all_crops, city_crops_mapping)
        
        # Raporu kaydet
        report_path = os.path.join(os.path.dirname(__file__), "final5_summary.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Özet raporu kaydedildi: {report_path}")
        
        # Özet
        print("\n📊 ÖZET")
        print("-" * 30)
        print(f"Orijinal veri: {df.shape[0]} satır, {df.shape[1]} sütun")
        print(f"Final veri: {df_final.shape[0]} satır, {df_final.shape[1]} sütun")
        print(f"Toplam ürün: {len(all_crops)}")
        print(f"Özellik sayısı: {df_final.shape[1] - len(all_crops)}")
        print(f"Label sayısı: {len(all_crops)}")
        
        print("\n🎉 Multi-label veri seti hazırlama tamamlandı!")
        print("📁 Çıktı dosyaları:")
        print(f"   - {final_path}")
        print(f"   - {os.path.join(os.path.dirname(__file__), 'final5_info.json')}")
        print(f"   - {report_path}")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
