from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import pandas as pd
import time
import random

class ImprovedMgmScraper:
    def __init__(self):
        self.setup_driver()
        self.base_url = "https://www.mgm.gov.tr/veridegerlendirme/il-ve-ilceler-istatistik.aspx?k=H"
        
    def setup_driver(self):
        """Driver'ı daha güvenli şekilde kur"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Ek stabilite ayarları
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)  # Daha uzun timeout
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            print(f"Driver başlatılırken hata: {e}")
            raise
    
    def restart_driver(self):
        """Driver'ı yeniden başlat"""
        print("Driver yeniden başlatılıyor...")
        try:
            self.driver.quit()
        except:
            pass
        time.sleep(3)  # Daha uzun bekleme
        self.setup_driver()
    
    def get_city_links(self):
        """Tüm şehir linklerini al"""
        print("Şehir linkleri alınıyor...")
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.driver.get(self.base_url)
                
                city_div = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "kk_div1"))
                )
                
                city_links = []
                links = city_div.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    city_name = link.text.strip()
                    if city_name:
                        city_url = link.get_attribute("href")
                        if city_url and city_url.startswith("?"):
                            city_url = "https://www.mgm.gov.tr/veridegerlendirme/il-ve-ilceler-istatistik.aspx" + city_url
                        city_links.append((city_name, city_url))
                
                print(f"{len(city_links)} şehir bulundu")
                return city_links
                
            except Exception as e:
                print(f"Şehir linkleri alınırken hata (deneme {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.restart_driver()
                else:
                    raise
    
    def scrape_city_data(self, city_name, city_url):
        """Bir şehrin verilerini scrape et - GELİŞTİRİLMİŞ"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                print(f"{city_name} verileri alınıyor... (deneme {attempt + 1})")
                
                # Exponential backoff - her denemede daha fazla bekle
                wait_time = random.uniform(2, 4) * (attempt + 1)
                time.sleep(wait_time)
                
                # Sayfayı yükle
                self.driver.get(city_url)
                
                # Sayfanın tamamen yüklendiğini doğrula
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # Tablonun yüklenmesini bekle - daha uzun timeout
                try:
                    table = WebDriverWait(self.driver, 40).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                except TimeoutException:
                    # Tablo yoksa, sayfada "veri yok" mesajı var mı kontrol et
                    page_text = self.driver.page_source.lower()
                    if "veri" in page_text or "yok" in page_text or len(self.driver.find_elements(By.TAG_NAME, "table")) == 0:
                        print(f"⚠️ {city_name} için MGM'de veri bulunmuyor - ATLANACAK")
                        return "NO_DATA"  # Özel işaret
                    raise
                
                # Tablonun içeriğinin yüklendiğini doğrula
                WebDriverWait(self.driver, 10).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "tr")) > 1
                )
                
                # Verileri topla
                city_data = {"Şehir": city_name}
                
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    header_cells = row.find_elements(By.TAG_NAME, "th")
                    if len(header_cells) > 0:
                        parameter = header_cells[0].text.strip()
                        if parameter and parameter != city_name:
                            
                            data_cells = row.find_elements(By.TAG_NAME, "td")
                            
                            for i, cell in enumerate(data_cells):
                                month = self.get_month_name(i)
                                if month:
                                    cell_id = f"{parameter}_{month}"
                                    value = cell.text.strip()
                                    city_data[cell_id] = value
                
                print(f"{city_name} verileri başarıyla alındı")
                return city_data
                
            except TimeoutException:
                print(f"⏱️ {city_name} için zaman aşımı (deneme {attempt + 1})")
                if attempt < max_retries - 1:
                    # Driver'ı yeniden başlat ve tekrar dene
                    self.restart_driver()
                    continue
                else:
                    print(f"⚠️ {city_name} için tüm denemeler başarısız")
                    return None
                    
            except WebDriverException as e:
                print(f"🔧 {city_name} için WebDriver hatası (deneme {attempt + 1})")
                if attempt < max_retries - 1:
                    self.restart_driver()
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"❌ {city_name} için beklenmeyen hata (deneme {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return None
        
        return None
    
    def get_month_name(self, index):
        """Ay indeksini ay ismine çevir"""
        months = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık", "Yıllık"
        ]
        return months[index] if index < len(months) else None
    
    def scrape_all_cities(self):
        """TÜM şehirleri scrape et - BAŞARISIZLARI TEKRAR DENE"""
        city_links = self.get_city_links()
        all_data = []
        failed_cities = []
        no_data_cities = []  # Veri olmayan şehirler
        
        total_cities = len(city_links)
        successful = 0
        
        print(f"🚀 TÜM ŞEHİRLER İŞLENİYOR: {total_cities} şehir")
        
        # İLK TUR
        for i, (city_name, city_url) in enumerate(city_links, 1):
            print(f"\n[{i}/{total_cities}] İşleniyor: {city_name}")
            
            city_data = self.scrape_city_data(city_name, city_url)
            if city_data == "NO_DATA":
                no_data_cities.append(city_name)
                print(f"⚠️ {city_name} - VERİ YOK (normal)")
            elif city_data:
                all_data.append(city_data)
                successful += 1
                print(f"✅ {city_name} - BAŞARILI")
            else:
                failed_cities.append((city_name, city_url))
                print(f"❌ {city_name} - BAŞARISIZ (tekrar denenecek)")
            
            # Her 10 şehirden sonra driver'ı yeniden başlat
            if i % 10 == 0 and i < total_cities:
                print(f"🔄 {i}. şehirden sonra driver yeniden başlatılıyor...")
                self.restart_driver()
                
            # İlerleme durumunu göster
            if i % 5 == 0:
                progress = (i / total_cities) * 100
                failed = len(failed_cities)
                print(f"📊 İlerleme: {i}/{total_cities} ({progress:.1f}%) - Başarılı: {successful}, Başarısız: {failed}, Veri Yok: {len(no_data_cities)}")
        
        # İKİNCİ TUR - BAŞARISIZ ŞEHİRLERİ TEKRAR DENE
        if failed_cities:
            print(f"\n{'='*60}")
            print(f"🔄 İKİNCİ TUR: {len(failed_cities)} başarısız şehir tekrar deneniyor...")
            print(f"{'='*60}\n")
            
            self.restart_driver()
            time.sleep(5)
            
            retry_failed = []
            for idx, (city_name, city_url) in enumerate(failed_cities, 1):
                print(f"\n[Tekrar {idx}/{len(failed_cities)}] İşleniyor: {city_name}")
                
                city_data = self.scrape_city_data(city_name, city_url)
                if city_data == "NO_DATA":
                    no_data_cities.append(city_name)
                    print(f"⚠️ {city_name} - VERİ YOK (ikinci denemede anlaşıldı)")
                elif city_data:
                    all_data.append(city_data)
                    successful += 1
                    print(f"✅ {city_name} - İKİNCİ DENEMEDE BAŞARILI!")
                else:
                    retry_failed.append((city_name, city_url))
                    print(f"❌ {city_name} - YİNE BAŞARISIZ")
                
                # Başarısız şehirler arasında da driver'ı yenile
                if idx % 5 == 0 and idx < len(failed_cities):
                    self.restart_driver()
                    time.sleep(3)
            
            failed_cities = retry_failed
        
        # SONUÇ RAPORU
        print(f"\n{'='*60}")
        print(f"🎉 TÜM ŞEHİRLER TAMAMLANDI!")
        print(f"{'='*60}")
        print(f"📊 Toplam: {total_cities} şehir")
        print(f"✅ Başarılı: {successful} şehir")
        print(f"⚠️ Veri Yok: {len(no_data_cities)} şehir")
        print(f"❌ Başarısız: {len(failed_cities)} şehir")
        
        actual_total = total_cities - len(no_data_cities)
        if actual_total > 0:
            print(f"📈 Başarı Oranı (veri olan şehirler): {(successful/actual_total)*100:.1f}%")
        
        if no_data_cities:
            print(f"\n⚠️ Veri olmayan şehirler (MGM'de kayıt yok):")
            for city_name in no_data_cities:
                print(f"   - {city_name}")
        
        if failed_cities:
            print(f"\n❌ Başarısız şehirler:")
            for city_name, _ in failed_cities:
                print(f"   - {city_name}")
            
            # Başarısız şehirleri dosyaya kaydet
            pd.DataFrame(failed_cities, columns=['Şehir', 'URL']).to_csv(
                'basarisiz_sehirler.csv', index=False, encoding='utf-8-sig'
            )
            print(f"\n💾 Başarısız şehirler 'basarisiz_sehirler.csv' dosyasına kaydedildi")
        else:
            print(f"\n🎊 VERİSİ OLAN TÜM ŞEHİRLER %100 BAŞARIYLA TAMAMLANDI!")
        
        return all_data
    
    def save_to_csv(self, data, filename="mgm_iklim_verileri.csv"):
        """Verileri CSV dosyasına kaydet"""
        if not data:
            print("Kaydedilecek veri bulunamadı!")
            return
        
        df = pd.DataFrame(data)
        
        columns = ["Şehir"] + [col for col in df.columns if col != "Şehir"]
        df = df[columns]
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Veriler {filename} dosyasına kaydedildi")
        print(f"📊 Toplam {len(data)} şehrin verisi kaydedildi")
        
        return df
    
    def close(self):
        """Driver'ı kapat"""
        try:
            self.driver.quit()
            print("Driver kapatıldı")
        except:
            pass

def main():
    scraper = ImprovedMgmScraper()
    
    try:
        print("🚀 TÜM ŞEHİRLER ALINIYOR...")
        all_data = scraper.scrape_all_cities()
        
        if all_data:
            df = scraper.save_to_csv(all_data)
            print("\n📋 İlk 5 satır önizleme:")
            print(df.head())
            print(f"\n📁 Dosya boyutu: {len(df)} satır, {len(df.columns)} sütun")
        else:
            print("❌ Hiç veri alınamadı!")
        
    except Exception as e:
        print(f"❌ Scraping sırasında hata oluştu: {str(e)}")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()