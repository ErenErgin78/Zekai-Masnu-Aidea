import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@dataclass
class Issue:
    """Dergi sayısı bilgilerini tutan veri sınıfı"""
    url: str
    text: str


@dataclass
class Article:
    """Makale bilgilerini tutan veri sınıfı"""
    url: str
    title: str


@dataclass
class DownloadStats:
    """İndirme istatistiklerini tutan veri sınıfı"""
    total_issues: int = 0
    total_articles: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0

    def print_summary(self):
        """İstatistik özetini yazdır"""
        print("\n" + "=" * 70)
        print("📊 İNDİRME İSTATİSTİKLERİ")
        print("=" * 70)
        print(f"Toplam Dergi Sayısı     : {self.total_issues}")
        print(f"Toplam Makale           : {self.total_articles}")
        print(f"Başarılı İndirmeler     : {self.successful_downloads}")
        print(f"Başarısız İndirmeler    : {self.failed_downloads}")
        print(f"Başarı Oranı            : {self._success_rate():.1f}%")
        print("=" * 70)

    def _success_rate(self) -> float:
        """Başarı oranını hesapla"""
        if self.total_articles == 0:
            return 0.0
        return (self.successful_downloads / self.total_articles) * 100


class DergiParkScraper:
    """DergiPark arşivinden PDF indirme sınıfı"""
    
    # Sabitler
    TIMEOUT = 20
    PAGE_LOAD_DELAY = 3
    DOWNLOAD_DELAY = 2
    MAX_FILENAME_LENGTH = 200
    
    def __init__(self, base_url: str, download_dir: str = "downloaded_pdfs"):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.stats = DownloadStats()
        self.driver = None
        self.wait = None
        
        self._setup_driver()
        self._create_download_directory()
    
    def _setup_driver(self):
        """Chrome driver'ı yapılandır"""
        chrome_options = webdriver.ChromeOptions()
        
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Performans optimizasyonları
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        
        print("✓ Chrome driver başarıyla yapılandırıldı")
    
    def _create_download_directory(self):
        """İndirme dizinini oluştur"""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ İndirme dizini hazır: {self.download_dir}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Dosya adını temizle ve geçerli hale getir"""
        # Geçersiz karakterleri kaldır
        clean = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        clean = clean.strip()
        
        # Baştaki numarayı kaldır (örn: "1. Makale" -> "Makale")
        if clean and clean[0].isdigit() and '.' in clean[:5]:
            clean = clean.split('.', 1)[1].strip()
        
        # Uzunluk sınırı
        if len(clean) > self.MAX_FILENAME_LENGTH:
            clean = clean[:self.MAX_FILENAME_LENGTH]
        
        return clean
    
    def _get_unique_filepath(self, filepath: Path) -> Path:
        """Eğer dosya varsa benzersiz bir isim oluştur"""
        if not filepath.exists():
            return filepath
        
        counter = 1
        stem = filepath.stem
        suffix = filepath.suffix
        
        while filepath.exists():
            filepath = filepath.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        return filepath
    
    def get_issue_links(self) -> List[Issue]:
        """Arşiv sayfasındaki tüm dergi sayılarının linklerini al"""
        print("\n" + "=" * 70)
        print("📚 ARŞİV SAYFASI TARANILIYOR")
        print("=" * 70)
        
        self.driver.get(self.base_url)
        time.sleep(self.PAGE_LOAD_DELAY)
        
        issues = []
        
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            
            for row in rows:
                try:
                    link_element = row.find_element(By.CSS_SELECTOR, "a[href*='/issue/']")
                    issue_url = link_element.get_attribute('href')
                    issue_text = link_element.text.strip()
                    
                    if issue_url and '/issue/' in issue_url:
                        issues.append(Issue(url=issue_url, text=issue_text))
                        print(f"  ✓ {issue_text}")
                        
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            print(f"  ✗ Hata: {e}")
        
        self.stats.total_issues = len(issues)
        print(f"\n📊 Toplam {len(issues)} dergi sayısı bulundu")
        
        return issues
    
    def get_article_links_from_issue(self, issue: Issue) -> List[Article]:
        """Bir dergi sayfasındaki tüm makale linklerini al"""
        print(f"\n  📄 {issue.text}")
        print(f"  URL: {issue.url}")
        
        self.driver.get(issue.url)
        time.sleep(self.PAGE_LOAD_DELAY)
        
        articles = []
        
        try:
            cards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".card.j-card.article-project-actions"
            )
            
            for card in cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a.card-title.article-title")
                    article_url = link.get_attribute('href')
                    article_title = link.text.strip()
                    
                    if article_url and '/issue/' in article_url:
                        articles.append(Article(url=article_url, title=article_title))
                        
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            print(f"    ✗ Hata: {e}")
        
        self.stats.total_articles += len(articles)
        print(f"  📊 {len(articles)} makale bulundu")
        
        return articles
    
    def download_pdf_from_article(self, article: Article, index: int, total: int):
        """Makale sayfasındaki PDF'i indir"""
        print(f"\n    [{index}/{total}] {article.title[:60]}...")
        
        self.driver.get(article.url)
        time.sleep(self.PAGE_LOAD_DELAY)
        
        try:
            # PDF butonunu bul
            pdf_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.btn.btn-sm.float-left.article-tool.pdf")
                )
            )
            
            pdf_url = pdf_button.get_attribute('href')
            if not pdf_url.startswith('http'):
                pdf_url = 'https://dergipark.org.tr' + pdf_url
            
            self._download_pdf_file(pdf_url, article.title)
            
        except TimeoutException:
            print(f"      ⚠ PDF butonu bulunamadı, alternatif yöntem deneniyor...")
            self._find_pdf_alternative(article)
        except Exception as e:
            print(f"      ✗ Hata: {e}")
            self.stats.failed_downloads += 1
    
    def _find_pdf_alternative(self, article: Article):
        """Alternatif PDF bulma yöntemi"""
        try:
            pdf_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[href*='/download/article-file/']"
            )
            
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute('href')
                if not pdf_url.startswith('http'):
                    pdf_url = 'https://dergipark.org.tr' + pdf_url
                
                self._download_pdf_file(pdf_url, article.title)
            else:
                print(f"      ✗ PDF bulunamadı")
                self.stats.failed_downloads += 1
                
        except Exception as e:
            print(f"      ✗ Alternatif arama hatası: {e}")
            self.stats.failed_downloads += 1
    
    def _download_pdf_file(self, pdf_url: str, article_title: str):
        """PDF dosyasını indir ve kaydet"""
        try:
            clean_title = self._sanitize_filename(article_title)
            filename = f"{clean_title}.pdf"
            filepath = self._get_unique_filepath(self.download_dir / filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://dergipark.org.tr/'
            }
            
            session = requests.Session()
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            response = session.get(pdf_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size_kb = filepath.stat().st_size / 1024
            print(f"      ✓ İndirildi: {filepath.name} ({file_size_kb:.1f} KB)")
            self.stats.successful_downloads += 1
            
        except Exception as e:
            print(f"      ✗ İndirme hatası: {e}")
            self.stats.failed_downloads += 1
    
    def scrape_all_issues(self):
        """Tüm dergi sayılarını ve makaleleri tarar"""
        print("\n" + "=" * 70)
        print("🚀 DERGİPARK SCRAPING İŞLEMİ BAŞLATILIYOR")
        print("=" * 70)
        
        issues = self.get_issue_links()
        
        for i, issue in enumerate(issues, 1):
            print(f"\n{'=' * 70}")
            print(f"📖 [{i}/{len(issues)}] İşleniyor")
            print(f"{'=' * 70}")
            
            try:
                articles = self.get_article_links_from_issue(issue)
                
                for j, article in enumerate(articles, 1):
                    self.download_pdf_from_article(article, j, len(articles))
                    time.sleep(self.DOWNLOAD_DELAY)
                    
            except Exception as e:
                print(f"  ✗ Dergi işlenirken hata: {e}")
                continue
        
        self.stats.print_summary()
        print(f"\n💾 PDF'ler '{self.download_dir}' klasörüne kaydedildi")
    
    def close(self):
        """Kaynakları temizle"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Tarayıcı kapatıldı")


def main():
    """Ana fonksiyon"""
    BASE_URL = "https://dergipark.org.tr/tr/pub/tbbbd/archive"
    DOWNLOAD_DIR = "dergipark_pdfs"
    
    scraper = None
    
    try:
        scraper = DergiParkScraper(BASE_URL, DOWNLOAD_DIR)
        scraper.scrape_all_issues()
        
    except KeyboardInterrupt:
        print("\n\n⚠ İşlem kullanıcı tarafından durduruldu")
        
    except Exception as e:
        print(f"\n✗ Kritik hata: {e}")
        
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()