from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os
import time
import re

class DRTScraper:
    def __init__(self):
        self.base_url = "https://www.drt.com.tr"
        self.main_url = "https://www.drt.com.tr/faydali-bilgiler/"
        
        # Selenium WebDriver ayarları
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Tarayıcıyı gizli modda çalıştır
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Logları azalt
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def clean_filename(self, filename):
        """Dosya adını temizle ve geçerli hale getir"""
        # Türkçe karakterleri düzelt
        filename = filename.replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i')
        filename = filename.replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
        filename = filename.replace('Ç', 'C').replace('Ğ', 'G').replace('İ', 'I')
        filename = filename.replace('Ö', 'O').replace('Ş', 'S').replace('Ü', 'U')
        
        # Geçersiz karakterleri kaldır
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip()
        
        # Uzunluk sınırlaması
        if len(filename) > 100:
            filename = filename[:100]
            
        return filename
    
    def get_article_urls_from_html(self, html_content):
        """HTML içeriğinden makale URL'lerini çıkar"""
        soup = BeautifulSoup(html_content, 'html.parser')
        article_urls = []
        
        # 1. Yöntem: heading içindeki linkleri bul
        headings = soup.find_all('h2', class_='elementor-heading-title')
        for heading in headings:
            link = heading.find('a', href=True)
            if link:
                href = link['href']
                if href not in article_urls and 'drt.com.tr' in href:
                    article_urls.append(href)
        
        # 2. Yöntem: jet-listing-grid içindeki tüm a etiketleri
        listing_grid = soup.find('div', class_='jet-listing-grid')
        if listing_grid:
            links = listing_grid.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href not in article_urls and 'drt.com.tr' in href and '/wp-content/' not in href:
                    article_urls.append(href)
        
        # 3. Yöntem: elementor-post başlıklı tüm a etiketleri
        post_links = soup.find_all('a', class_=lambda x: x and 'elementor-post' in x)
        for link in post_links:
            if 'href' in link.attrs:
                href = link['href']
                if href not in article_urls and 'drt.com.tr' in href:
                    article_urls.append(href)
        
        return list(set(article_urls))
    
    def wait_for_pagination(self):
        """Pagination yüklenene kadar bekle"""
        try:
            # Pagination item'larının yüklenmesini bekle
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "jet-filters-pagination__item"))
            )
            time.sleep(1)  # JavaScript'in tam yüklenmesi için ekstra süre
            return True
        except TimeoutException:
            print("  ⚠ Pagination yüklenmedi")
            return False
    
    def has_next_button(self, debug=False):
        """Sonraki butonu var mı kontrol et - Selenium ile"""
        try:
            # Önce pagination'ın yüklenmesini bekle
            self.wait_for_pagination()
            
            if debug:
                print("\n  🔍 BUTON TESPİT DETAYLARI:")
                print("  " + "-" * 50)
            
            # Tüm pagination item'larını bul
            items = self.driver.find_elements(By.CLASS_NAME, "jet-filters-pagination__item")
            
            if debug:
                print(f"  ✓ Toplam {len(items)} pagination item bulundu")
                for idx, item in enumerate(items, 1):
                    classes = item.get_attribute('class')
                    data_value = item.get_attribute('data-value')
                    text = item.text.strip()
                    print(f"    [{idx}] class='{classes}' | data-value='{data_value}' | text='{text}'")
                print("  " + "-" * 50)
            
            # Sonraki butonunu ara
            for item in items:
                data_value = item.get_attribute('data-value')
                classes = item.get_attribute('class')
                
                if data_value == 'next' or 'next' in classes:
                    if debug:
                        print("  ✓ SONUÇ: Sonraki butonu BULUNDU!\n")
                    return True
            
            if debug:
                print("  ✗ SONUÇ: Sonraki butonu YOK\n")
            return False
            
        except Exception as e:
            if debug:
                print(f"  ✗ Hata: {e}\n")
            return False
    
    def click_next_button(self):
        """Sonraki butonuna tıkla"""
        try:
            # Sonraki butonunu bul
            next_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                ".jet-filters-pagination__item[data-value='next']"
            )
            
            # Butona kaydır (ortaya gelsin)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)
            
            # Yöntem 1: JavaScript ile tıkla (en güvenilir)
            try:
                self.driver.execute_script("arguments[0].click();", next_button)
                print("  ✓ Sonraki butonuna tıklandı (JavaScript)")
            except Exception as e1:
                print(f"  ⚠ JavaScript tıklama başarısız, alternatif yöntem deneniyor...")
                
                # Yöntem 2: Normal tıklama
                try:
                    next_button.click()
                    print("  ✓ Sonraki butonuna tıklandı (Normal)")
                except Exception as e2:
                    print(f"  ⚠ Normal tıklama başarısız, ActionChains deneniyor...")
                    
                    # Yöntem 3: ActionChains ile tıkla
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(next_button).click().perform()
                    print("  ✓ Sonraki butonuna tıklandı (ActionChains)")
            
            # AJAX yüklemesinin bitmesini bekle
            print("  ⏳ Sayfa yükleniyor...")
            time.sleep(4)  # AJAX için daha uzun süre
            
            # Yeni içeriğin yüklenmesini bekle
            self.wait_for_pagination()
            
            return True
            
        except NoSuchElementException:
            print("  ✗ Sonraki butonu bulunamadı")
            return False
        except Exception as e:
            print(f"  ✗ Tıklama hatası: {e}")
            return False
    
    def get_all_article_urls(self):
        """Tüm sayfalardaki makale URL'lerini topla - Selenium ile"""
        all_urls = []
        page_num = 1
        
        print("Makale URL'leri toplanıyor...\n")
        
        # İlk sayfayı aç
        print(f"--- Sayfa {page_num} ---")
        print(f"URL açılıyor: {self.main_url}")
        self.driver.get(self.main_url)
        
        # Pagination yüklenmesini bekle
        self.wait_for_pagination()
        
        # İlk sayfadaki makaleleri al
        current_html = self.driver.page_source
        page_urls = self.get_article_urls_from_html(current_html)
        all_urls.extend(page_urls)
        print(f"✓ {len(page_urls)} makale bulundu")
        
        # Sonraki butonu var mı kontrol et
        has_next = self.has_next_button(debug=True)
        print(f"Sonraki butonu: {'✓ VAR' if has_next else '✗ YOK'}")
        
        # Sonraki butonu oldukça devam et
        while has_next:
            page_num += 1
            print(f"\n--- Sayfa {page_num} ---")
            
            # Sonraki butonuna tıkla
            if self.click_next_button():
                # Makaleleri al
                current_html = self.driver.page_source
                page_urls = self.get_article_urls_from_html(current_html)
                
                if page_urls:
                    all_urls.extend(page_urls)
                    print(f"✓ {len(page_urls)} makale bulundu")
                else:
                    print("✗ Bu sayfada makale bulunamadı")
                
                # Sonraki butonu hala var mı?
                has_next = self.has_next_button(debug=True)
                print(f"Sonraki butonu: {'✓ VAR' if has_next else '✗ YOK'}")
                
                if not has_next:
                    print("\n→ Sonraki butonu kayboldu, pagination tamamlandı!")
                    break
            else:
                print("✗ Sonraki buton tıklanamadı, duruluyor...")
                break
            
            # Sonsuz döngü önleme
            if page_num >= 50:
                print("\n⚠ Maksimum sayfa sayısına ulaşıldı (50), duruluyor...")
                break
        
        # Tekilleştir
        unique_urls = list(set(all_urls))
        print(f"\n{'=' * 60}")
        print(f"✓ Toplam {len(unique_urls)} benzersiz makale bulundu")
        print(f"{'=' * 60}")
        return unique_urls
    
    def scrape_article_content(self, article_url):
        """Bir makalenin içeriğini çek"""
        try:
            self.driver.get(article_url)
            time.sleep(2)  # Sayfa yüklenmesini bekle
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Başlığı al
            title_element = soup.find('h1') or soup.find('h2', class_='elementor-heading-title')
            title = title_element.get_text().strip() if title_element else "Başlıksız Makale"
            
            # İçeriği al
            content_div = soup.find('div', class_='elementor-widget-theme-post-content')
            if not content_div:
                content_div = soup.find('div', class_='elementor-widget-text-editor')
            
            content_text = ""
            if content_div:
                paragraphs = content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text:
                        content_text += text + "\n\n"
            
            # Yedek yöntem
            if not content_text.strip():
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_text += text + "\n\n"
            
            return title, content_text.strip()
            
        except Exception as e:
            print(f"    ✗ Makale çekme hatası: {e}")
            return None, None
    
    def save_article_to_file(self, title, content, index, total):
        """Makaleyi txt dosyasına kaydet"""
        if not content:
            return False
        
        clean_title = self.clean_filename(title)
        filename = f"{index:03d}_{clean_title}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Başlık: {title}\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(content)
            
            print(f"    ✓ Kaydedildi: {filename}")
            return True
            
        except Exception as e:
            print(f"    ✗ Kaydetme hatası: {e}")
            return False
    
    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("DRT Scraper - Selenium ile Pagination")
        print("=" * 60 + "\n")
        
        try:
            # Çıktı klasörü oluştur
            if not os.path.exists('drt_makaleler'):
                os.makedirs('drt_makaleler')
            os.chdir('drt_makaleler')
            
            # Tüm makale URL'lerini al
            article_urls = self.get_all_article_urls()
            
            if not article_urls:
                print("✗ Hiç makale bulunamadı!")
                return
            
            print(f"\n{'=' * 60}")
            print(f"Makale içerikleri indiriliyor...")
            print(f"{'=' * 60}\n")
            
            # Her makaleyi işle
            success_count = 0
            for i, url in enumerate(article_urls, 1):
                print(f"[{i}/{len(article_urls)}] {url}")
                
                title, content = self.scrape_article_content(url)
                
                if title and content:
                    if self.save_article_to_file(title, content, i, len(article_urls)):
                        success_count += 1
                else:
                    print(f"    ✗ İçerik çekilemedi")
                
                time.sleep(1)
            
            print(f"\n{'=' * 60}")
            print(f"İşlem Tamamlandı!")
            print(f"Başarılı: {success_count}/{len(article_urls)}")
            print(f"Klasör: drt_makaleler/")
            print(f"{'=' * 60}")
            
        finally:
            # Tarayıcıyı kapat
            print("\nTarayıcı kapatılıyor...")
            self.driver.quit()

if __name__ == "__main__":
    scraper = DRTScraper()
    scraper.run()