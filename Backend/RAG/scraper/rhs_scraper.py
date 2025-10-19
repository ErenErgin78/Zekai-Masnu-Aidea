from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
from datetime import datetime

class RHSScraper:
    def __init__(self):
        # Chrome seçeneklerini ayarla
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Tarayıcıyı gösterme (isterseniz kaldırabilirsiniz)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.base_url = "https://www.rhs.org.uk"
        self.advice_url = f"{self.base_url}/advice/advice-search"
        self.wait = WebDriverWait(self.driver, 10)
        
        # Veri kaydetme klasörü - mutlak yol kullan
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(script_dir, "rhs_scraped_data")
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📁 Veri klasörü: {self.output_dir}")
        
    def get_categories(self):
        """Tüm kategorileri al"""
        print("Kategoriler alınıyor...")
        self.driver.get(self.advice_url)
        time.sleep(3)
        
        categories = []
        try:
            # Kategori checkbox'larını bul
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 
                "filter-list-item input[type='checkbox']:not([disabled])")
            
            for checkbox in checkboxes:
                checkbox_id = checkbox.get_attribute('id')
                label = self.driver.find_element(By.CSS_SELECTOR, 
                    f"label[for='{checkbox_id}'] .form-checkbox__text")
                
                category_text = label.text
                category_name = category_text.split('(')[0].strip()
                
                categories.append({
                    'id': checkbox_id,
                    'name': category_name,
                    'full_text': category_text
                })
                
            print(f"{len(categories)} kategori bulundu.")
            return categories
            
        except Exception as e:
            print(f"Kategori alma hatası: {e}")
            return []
    
    def click_category(self, category_id):
        """Belirli bir kategoriye tıkla"""
        try:
            # Label'ı bul ve ona tıkla
            label = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='{category_id}']"))
            )
            
            # Sayfayı scroll et (görünür hale getir)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", label)
            time.sleep(0.5)
            
            # JavaScript ile tıkla
            self.driver.execute_script("arguments[0].click();", label)
            
            # Sayfanın güncellenmesini bekle - loading sınıfının kaybolmasını bekle
            time.sleep(2)
            
            # Loading animasyonunun bitmesini kontrol et
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "advice-list .gl-view"))
                )
                print("  ✓ Kategori seçildi ve makaleler yüklendi")
            except TimeoutException:
                print("  ⚠ Makaleler yüklenirken zaman aşımı")
            
            time.sleep(1)  # Ek güvenlik bekleme
            
            return True
        except Exception as e:
            print(f"  ✗ Kategori tıklama hatası: {e}")
            # Alternatif yöntem: Doğrudan checkbox'a tıkla
            try:
                checkbox = self.driver.find_element(By.ID, category_id)
                self.driver.execute_script("arguments[0].checked = true;", checkbox)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", checkbox)
                time.sleep(3)
                print("  ✓ Alternatif yöntemle kategori seçildi")
                return True
            except Exception as e2:
                print(f"  ✗ Alternatif yöntem de başarısız: {e2}")
                return False
    
    def get_article_links(self):
        """Sayfadaki tüm makale linklerini al"""
        article_links = []
        try:
            # Sayfa yüklenene kadar bekle - loading sınıfı kaybolsun
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "advice-list"))
            )
            
            # Loading animasyonunun bitmesini bekle
            time.sleep(2)
            
            # Makalelerin yüklendiğinden emin ol
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "advice-list-item"))
                )
            except TimeoutException:
                print("  Hiç makale bulunamadı (timeout)")
                return []
            
            # INFINITE SCROLL - Tüm makaleleri yükle
            print("  ⏳ Tüm makaleler yükleniyor (infinite scroll)...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            articles_count = 0
            no_change_count = 0
            
            while True:
                # Sayfanın en altına scroll yap
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Yeni içeriğin yüklenmesi için bekle
                
                # Yeni yüksekliği kontrol et
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Makale sayısını kontrol et
                current_articles = len(self.driver.find_elements(By.CSS_SELECTOR, "advice-list-item"))
                
                if current_articles > articles_count:
                    print(f"    📄 {current_articles} makale yüklendi...")
                    articles_count = current_articles
                    no_change_count = 0
                else:
                    no_change_count += 1
                
                # Eğer sayfa yüksekliği değişmediyse veya 3 kez üst üste değişim olmadıysa bitir
                if new_height == last_height or no_change_count >= 3:
                    print(f"  ✓ Tüm makaleler yüklendi (toplam: {articles_count})")
                    break
                
                last_height = new_height
                
                # Güvenlik için maksimum 50 scroll
                if no_change_count >= 50:
                    print("  ⚠ Maksimum scroll sayısına ulaşıldı")
                    break
            
            # En üste geri dön
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Tüm makale elementlerini bul
            article_items = self.driver.find_elements(By.CSS_SELECTOR, "advice-list-item")
            
            for item in article_items:
                try:
                    # Title'ı al
                    title_elem = item.find_element(By.CSS_SELECTOR, "h4.gl-view__title")
                    title = title_elem.text.strip()
                    
                    # Link'i al
                    link_elem = item.find_element(By.CSS_SELECTOR, "a.u-faux-block-link__overlay")
                    href = link_elem.get_attribute('href')
                    
                    # Boş title'ları atla (test sayfaları vs.)
                    if href and title:
                        article_links.append({
                            'url': href if href.startswith('http') else f"{self.base_url}{href}",
                            'title': title
                        })
                except NoSuchElementException:
                    continue
            
            print(f"  ✅ {len(article_links)} makale bulundu.")
            return article_links
            
        except Exception as e:
            print(f"Makale linkleri alma hatası: {e}")
            return []
    
    def scrape_article(self, article_url, article_title):
        """Tek bir makaleyi scrape et"""
        try:
            self.driver.get(article_url)
            time.sleep(2)
            
            article_data = {
                'url': article_url,
                'title': article_title,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Quick facts - düz metin olarak
            try:
                quick_facts_div = self.driver.find_element(By.CSS_SELECTOR, 
                    "div.panel--border .content")
                article_data['quick_facts'] = quick_facts_div.text.strip()
            except NoSuchElementException:
                article_data['quick_facts'] = ""
            
            # Ana içerik bölümleri - temiz metin
            sections = []
            try:
                section_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[id^='section-']")
                
                for section in section_containers:
                    try:
                        heading = section.find_element(By.TAG_NAME, 'h3').text
                        
                        # İçeriği temiz metin olarak al
                        content_elem = section.find_element(By.CSS_SELECTOR, '.content-steps')
                        content_text = content_elem.text.strip()
                        
                        # Resimleri al (eğer varsa)
                        images = []
                        try:
                            img_elements = section.find_elements(By.CSS_SELECTOR, 'img')
                            for img in img_elements:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or img.get_attribute('title')
                                if img_src and not img_src.endswith('ng-lazyloading'):
                                    images.append({
                                        'src': img_src,
                                        'alt': img_alt
                                    })
                        except:
                            pass
                        
                        sections.append({
                            'heading': heading,
                            'content': content_text,
                            'images': images
                        })
                    except NoSuchElementException:
                        continue
                        
            except NoSuchElementException:
                pass
            
            article_data['sections'] = sections
            
            # "See also" bölümü
            try:
                see_also = self.driver.find_element(By.CSS_SELECTOR, "div[id='section-200']")
                article_data['see_also'] = see_also.text.strip()
            except NoSuchElementException:
                article_data['see_also'] = ""
            
            # Metadata
            try:
                # Kategori label
                category = self.driver.find_element(By.CSS_SELECTOR, "h5.label").text
                article_data['category'] = category
            except NoSuchElementException:
                article_data['category'] = ""
            
            return article_data
            
        except Exception as e:
            print(f"  ❌ Makale scrape hatası ({article_title}): {e}")
            return None
    
    def save_data(self, data, filename):
        """Veriyi JSON olarak kaydet"""
        # Klasörün var olduğundan emin ol
        os.makedirs(self.output_dir, exist_ok=True)
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Sadece kategori dosyaları için mesaj göster
            if not filename.startswith('scraping_summary'):
                article_count = data.get('article_count', 0)
                print(f"  💾 Kaydedildi: {filename} ({article_count} makale)")
        except Exception as e:
            print(f"  ❌ Kayıt hatası ({filename}): {e}")
            print(f"     Denenen yol: {os.path.abspath(filepath)}")
    
    def scrape_all(self):
        """Tüm kategorileri ve makaleleri scrape et"""
        start_time = datetime.now()
        
        print("\n" + "=" * 70)
        print("🌱 RHS ADVICE SCRAPER".center(70))
        print("=" * 70)
        
        categories = self.get_categories()
        
        all_data = {
            'scraped_at': start_time.isoformat(),
            'total_categories': len(categories),
            'categories': [],
            'statistics': {}
        }
        
        total_articles_scraped = 0
        successful_scrapes = 0
        failed_scrapes = 0
        
        for idx, category in enumerate(categories, 1):
            print(f"\n┌{'─' * 68}┐")
            print(f"│ 📂 [{idx}/{len(categories)}] {category['name']:<60} │")
            print(f"└{'─' * 68}┘")
            
            # Ana sayfaya dön
            self.driver.get(self.advice_url)
            time.sleep(2)
            
            # Kategoriyi seç
            if not self.click_category(category['id']):
                continue
            
            # Makale linklerini al
            article_links = self.get_article_links()
            
            category_data = {
                'name': category['name'],
                'id': category['id'],
                'article_count': len(article_links),
                'articles': []
            }
            
            # Her makaleyi scrape et
            category_success = 0
            category_failed = 0
            
            for art_idx, article in enumerate(article_links, 1):
                progress = f"[{art_idx}/{len(article_links)}]"
                title_truncated = article['title'][:50] + "..." if len(article['title']) > 50 else article['title']
                print(f"  {progress:>10} 📄 {title_truncated}")
                
                article_data = self.scrape_article(article['url'], article['title'])
                
                if article_data:
                    category_data['articles'].append(article_data)
                    category_success += 1
                    successful_scrapes += 1
                else:
                    category_failed += 1
                    failed_scrapes += 1
                    
                time.sleep(1)  # Kibar scraping için bekleme
            
            total_articles_scraped += len(article_links)
            
            # Kategori özeti
            print(f"\n  ✅ Kategori tamamlandı: {category_success} başarılı, {category_failed} başarısız")
            
            # Kategori verilerini kaydet
            safe_name = category['name'].replace('/', '_').replace(' ', '_').lower()
            self.save_data(category_data, f"category_{safe_name}.json")
            
            all_data['categories'].append({
                'name': category['name'],
                'article_count': len(category_data['articles']),
                'successful': category_success,
                'failed': category_failed
            })
        
        # İstatistikleri hesapla
        end_time = datetime.now()
        duration = end_time - start_time
        
        all_data['statistics'] = {
            'total_articles_found': total_articles_scraped,
            'successful_scrapes': successful_scrapes,
            'failed_scrapes': failed_scrapes,
            'success_rate': f"{(successful_scrapes / total_articles_scraped * 100):.2f}%" if total_articles_scraped > 0 else "0%",
            'duration': str(duration).split('.')[0],  # HH:MM:SS formatında
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        # Genel özet kaydet
        self.save_data(all_data, "scraping_summary.json")
        
        # Final özet
        print("\n" + "=" * 70)
        print("✨ SCRAPING TAMAMLANDI!".center(70))
        print("=" * 70)
        print(f"\n📊 İSTATİSTİKLER:")
        print(f"   ├─ Toplam Kategori      : {len(categories)}")
        print(f"   ├─ Toplam Makale        : {total_articles_scraped}")
        print(f"   ├─ Başarılı Scrape      : {successful_scrapes} ✅")
        print(f"   ├─ Başarısız Scrape     : {failed_scrapes} ❌")
        print(f"   ├─ Başarı Oranı         : {all_data['statistics']['success_rate']}")
        print(f"   └─ Toplam Süre          : {all_data['statistics']['duration']}")
        
        print(f"\n💾 KAYDEDILEN DOSYALAR:")
        print(f"   ├─ Kategori JSON'ları   : {len(categories)} dosya")
        print(f"   ├─ Özet dosyası         : scraping_summary.json")
        print(f"   └─ Konum                : {os.path.abspath(self.output_dir)}/")
        
        print(f"\n🎯 EN ÇOK MAKALE İÇEREN KATEGORİLER:")
        sorted_categories = sorted(all_data['categories'], key=lambda x: x['article_count'], reverse=True)[:5]
        for i, cat in enumerate(sorted_categories, 1):
            print(f"   {i}. {cat['name']:<30} : {cat['article_count']} makale")
        
        print("\n" + "=" * 70 + "\n")
    
    def close(self):
        """Tarayıcıyı kapat"""
        self.driver.quit()


# Kullanım
if __name__ == "__main__":
    scraper = RHSScraper()
    try:
        scraper.scrape_all()
    finally:
        scraper.close()