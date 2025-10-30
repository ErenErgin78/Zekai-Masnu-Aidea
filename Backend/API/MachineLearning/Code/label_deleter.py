import pandas as pd

def drop_column_from_csv(input_file_path, column_name_to_drop, output_file_path):
    """
    Belirtilen CSV dosyasını yükler, belirtilen sütunu siler ve temizlenmiş veriyi
    yeni bir CSV dosyasına kaydeder.
    """
    print(f"'{input_file_path}' dosyası yükleniyor...")
    
    try:
        # CSV dosyasını oku
        df = pd.read_csv(input_file_path)
    except FileNotFoundError:
        print(f"HATA: Dosya bulunamadı: '{input_file_path}'")
        return
    
    # Silinecek sütunun dosyada olup olmadığını kontrol et
    if column_name_to_drop not in df.columns:
        print(f"HATA: '{column_name_to_drop}' adlı sütun dosyada bulunamadı. Lütfen sütun adını kontrol edin.")
        print(f"Mevcut sütunlar: {list(df.columns)}")
        return

    # Sütunu sil (axis=1 sütun silindiğini belirtir)
    df_dropped = df.drop(columns=[column_name_to_drop], axis=1)
    
    # Yeni dosyaya kaydet
    df_dropped.to_csv(output_file_path, index=False, encoding='utf-8-sig')

    print(f"\nİşlem Başarılı!")
    print(f"Silinen sütun: '{column_name_to_drop}'")
    print(f"Yeni dosya şuraya kaydedildi: '{output_file_path}'")
    print(f"Orijinal sütun sayısı: {len(df.columns)}, Yeni sütun sayısı: {len(df_dropped.columns)}")

# --- Kullanım ---
# Lütfen dosya adlarını ve sütun adını kendi verinize göre güncelleyin.
input_csv = 'final3.csv'  # Giriş dosyanızın adı
column_to_drop = 'plant'    # Silmek istediğiniz sütunun adı
output_csv = 'final3.csv' # Çıktı dosyasının adı

# Fonksiyonu çalıştır
drop_column_from_csv(input_csv, column_to_drop, output_csv)