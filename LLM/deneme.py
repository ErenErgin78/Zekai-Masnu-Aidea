import asyncio
from winsdk.windows.devices.geolocation import Geolocator, PositionStatus

async def get_windows_location():
    """Windows Konum Servisi'nden konumu alır."""
    
    print("Konum servisine erişim isteniyor...")
    # Cihazın konum servisine erişim izni iste
    access_status = await Geolocator.request_access_async()

    if access_status == 0: # Denied
        print("Hata: Konum izni reddedildi. Ayarlar > Gizlilik > Konum'dan izin verin.")
        return
    elif access_status == 3: # Unspecified error
        print("Hata: Konum alınırken belirtilmemiş bir hata oluştu.")
        return
    elif access_status == 2: # NotDetermined (Bu senaryoda izin istenir)
        print("Lütfen açılan pencereden konum iznini onaylayın.")
        # Kullanıcıdan yanıt beklenir, ancak betik burada beklemeyebilir.
        # Tekrar çalıştırmak gerekebilir.

    print("Konum bilgisi alınıyor...")
    geolocator = Geolocator()
    
    try:
        # Konum bilgisini al
        pos = await geolocator.get_geoposition_async()
        coord = pos.coordinate
        
        print(f"--- Konum Alındı ---")
        print(f"Enlem (Latitude):   {coord.point.position.latitude}")
        print(f"Boylam (Longitude):  {coord.point.position.longitude}")
        print(f"Doğruluk (Accuracy): {coord.accuracy} metre")
        
    except Exception as e:
        print(f"Konum alınamadı. Konum servisinizin açık olduğundan emin olun.")
        print(f"Hata detayı: {e}")

if __name__ == "__main__":
    # Windows'ta bu betiği çalıştırmak için:
    try:
        asyncio.run(get_windows_location())
    except Exception as e:
        print(f"Asyncio hatası: {e}")