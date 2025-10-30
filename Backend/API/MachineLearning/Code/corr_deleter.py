import pandas as pd
import numpy as np

def remove_high_correlation_columns_selective(file_path, correlation_threshold=0.85, output_suffix="_selectively_cleaned"):
    """
    Yüksek korelasyonlu sütunları (>= eşik) belirler ve her çift için 
    hangisini sileceğine daha stratejik karar verir: 
    Diğer sütunlarla en çok yüksek korelasyona sahip olanı siler.
    """
    print(f"--- Stratejik Korelasyon Analizi Başladı (Eşik: {correlation_threshold}) ---")
    
    try:
        # CSV dosyasını yükle
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"HATA: Dosya bulunamadı: '{file_path}'")
        return
    except Exception as e:
        print(f"HATA: Dosya okunurken bir sorun oluştu: {e}")
        return

    # 1. Sadece sayısal sütunları seç
    df_numeric = df.select_dtypes(include=np.number)
    
    if df_numeric.empty:
        print("UYARI: Korelasyon hesaplamak için sayısal sütun bulunamadı.")
        return
    
    # 2. Mutlak korelasyon matrisini hesapla
    corr_matrix = df_numeric.corr().abs()

    # 3. Silinecek sütunların adlarını tutacak liste
    columns_to_drop = set()
    
    # Tüm yüksek korelasyonlu çiftleri kaydet (daha sonra karar vermek için)
    high_corr_pairs = []

    # Üst üçgen matrisi seç (tekrarları önlemek için)
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # 4. Yüksek korelasyonlu çiftleri topla
    for col1 in upper.columns:
        for col2 in upper.index:
            if col1 != col2 and upper.loc[col2, col1] >= correlation_threshold:
                high_corr_pairs.append((col2, col1))

    print(f"Toplam {len(high_corr_pairs)} adet yüksek korelasyonlu çift bulundu.")

    # 5. Stratejik Silme İşlemi (A-B çifti bulunduysa, hangisinin daha 'redundant' olduğuna karar ver)
    
    # Silme işlemi tamamlanana kadar döngüyü sürdür
    while high_corr_pairs:
        # Hangi sütunların kaç yüksek korelasyonlu çiftte yer aldığını say
        # Bu, her sütunun ne kadar 'gereksiz' bilgi taşıdığını gösterir.
        correlation_counts = {}
        for col1, col2 in high_corr_pairs:
            correlation_counts[col1] = correlation_counts.get(col1, 0) + 1
            correlation_counts[col2] = correlation_counts.get(col2, 0) + 1
            
        # En yüksek korelasyon sayısına sahip sütunu bul (yani en çok gereksiz bilgi taşıyanı)
        # Eğer sayılar eşitse, alfabetik olarak ilk geleni seçeriz (rastgele bir seçim)
        column_to_remove = max(correlation_counts, key=correlation_counts.get)
        
        columns_to_drop.add(column_to_remove)
        
        print(f"SİLİNİYOR: '{column_to_remove}' ({correlation_counts[column_to_remove]} çiftte yer alıyor)")
        
        # Bu sütunu içeren tüm çiftleri listeden çıkar (çünkü bu sütun artık silinmiştir)
        high_corr_pairs = [
            (col1, col2) for col1, col2 in high_corr_pairs 
            if col1 != column_to_remove and col2 != column_to_remove
        ]

    # 6. DataFrame'den sütunları sil
    if not columns_to_drop:
        print("\nEşik değerinin üzerinde yüksek korelasyonlu sütun bulunamadı. Silme yapılmadı.")
        df_cleaned = df
    else:
        # Orijinal DataFrame'den silinecek sütunları çıkar
        df_cleaned = df.drop(columns=columns_to_drop, errors='ignore')
        
        print(f"\n--- Toplam Silinen Sütun Sayısı ({len(columns_to_drop)}) ---")
        print(columns_to_drop)

    # 7. Sonucu kaydet
    base_name = file_path.rsplit('.', 1)[0]
    output_filename = f"{base_name}{output_suffix}.csv"
    df_cleaned.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\n--- İşlem Tamamlandı ---")
    print(f"Orijinal şekil: {df.shape}")
    print(f"Temizlenmiş şekil: {df_cleaned.shape}")
    print(f"Temizlenmiş dosya kaydedildi: '{output_filename}'")


# --- ÇALIŞTIRMA ---
if __name__ == "__main__":
    input_file = 'final2.csv'
    
    # Fonksiyonu çalıştır
    remove_high_correlation_columns_selective(file_path=input_file, correlation_threshold=0.85)