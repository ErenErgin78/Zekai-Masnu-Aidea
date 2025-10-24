# rag_processor.py - GELİŞTİRİLMİŞ & FIXED SÜRÜM
import os
import sys
import warnings
from pathlib import Path
from typing import List, Optional

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# PDF Fallback yükleyiciler - ÖNCE BUNLARI DENE
try:
    from langchain_community.document_loaders import (
        PyPDFLoader, 
        TextLoader,
        UnstructuredWordDocumentLoader
    )
    FALLBACK_LOADERS_AVAILABLE = True
except ImportError:
    FALLBACK_LOADERS_AVAILABLE = False
    print("⚠️ LangChain document loaders kullanılamıyor")

# PyMuPDF - En güvenilir PDF okuyucu
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF kullanılamıyor")

# Gelişmiş belge yükleyiciler - EN SON DENE
try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("⚠️ unstructured.io kullanılamıyor")

# Chroma import
try:
    from langchain_chroma import Chroma
    CHROMA_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
        CHROMA_AVAILABLE = True
    except ImportError:
        CHROMA_AVAILABLE = False
        print("❌ ChromaDB bulunamadı!")

warnings.filterwarnings('ignore')

class RAGProcessor:
    def __init__(self, pdfs_path="PDFs", vector_store_path="vector_store"):
        self.pdfs_path = pdfs_path
        self.vector_store_path = vector_store_path
        
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB kütüphanesi yüklenemedi!")
            
        print("🔧 Embeddings modeli yükleniyor...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        print("✅ Embeddings hazır")
        
        self.vector_store = None
        
        # Başlangıçta vektör veritabanını yükle
        self._try_load_vector_store()
        
    def _try_load_vector_store(self):
        """Vektör veritabanını yüklemeyi dene"""
        try:
            # Vektör store klasörünü kontrol et
            if not os.path.exists(self.vector_store_path):
                print(f"⚠️ Vektör klasörü bulunamadı: {self.vector_store_path}")
                return False
            
            # chroma.sqlite3 dosyasını kontrol et
            sqlite_file = os.path.join(self.vector_store_path, "chroma.sqlite3")
            if not os.path.exists(sqlite_file):
                print(f"⚠️ chroma.sqlite3 bulunamadı: {sqlite_file}")
                return False
            
            print(f"📂 Vektör veritabanı yükleniyor: {self.vector_store_path}")
            
            # Chroma'yı yükle
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
            
            # Test sorgusu yaparak kontrol et
            test_results = self.vector_store.similarity_search("test", k=1)
            
            if test_results:
                print(f"✅ Vektör veritabanı başarıyla yüklendi!")
                return True
            else:
                print("⚠️ Vektör veritabanı boş görünüyor")
                return False
                
        except Exception as e:
            print(f"⚠️ Vektör veritabanı yükleme hatası: {e}")
            self.vector_store = None
            return False
    
    def _get_all_document_files(self) -> List[Path]:
        """PDFs klasörü ve tüm alt klasörlerindeki desteklenen dosyaları bul"""
        pdfs_path = Path(self.pdfs_path)
        
        if not pdfs_path.exists():
            print(f"❌ PDFs klasörü bulunamadı: {self.pdfs_path}")
            return []
        
        # Desteklenen dosya uzantıları
        supported_extensions = {
            '.pdf', '.doc', '.docx', '.txt', 
            '.rtf', '.odt', '.pptx', '.ppt'
        }
        
        # Tüm alt klasörleri tarayarak dosyaları bul
        document_files = []
        for ext in supported_extensions:
            files = list(pdfs_path.rglob(f"*{ext}"))
            document_files.extend(files)
        
        # Benzersiz dosya listesi
        document_files = list(set(document_files))
        document_files.sort()
        
        print(f"🔍 Tarama tamamlandı. {len(document_files)} dosya bulundu.")
        return document_files
    
    def _load_pdf_with_pymupdf(self, file_path: Path) -> List[Document]:
        """PyMuPDF ile PDF yükleme - EN GÜVENİLİR YÖNTEM"""
        if not PYMUPDF_AVAILABLE:
            return []
            
        try:
            print(f"   📄 PyMuPDF ile yükleniyor: {file_path.name}")
            
            doc = fitz.open(file_path)
            documents = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    document = Document(
                        page_content=text,
                        metadata={
                            "source": str(file_path),
                            "file_name": file_path.name,
                            "file_type": ".pdf",
                            "page": page_num + 1,
                            "total_pages": len(doc),
                            "loader_type": "pymupdf"
                        }
                    )
                    documents.append(document)
            
            doc.close()
            print(f"   ✅ {len(documents)} sayfa yüklendi (PyMuPDF)")
            return documents
            
        except Exception as e:
            print(f"   ⚠️ PyMuPDF yükleme hatası: {e}")
            return []
    
    def _load_document_with_langchain(self, file_path: Path) -> List[Document]:
        """LangChain yükleyicileri ile belge yükleme"""
        if not FALLBACK_LOADERS_AVAILABLE:
            return []
            
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.pdf':
                print(f"   📄 LangChain PDF Loader: {file_path.name}")
                loader = PyPDFLoader(str(file_path))
            elif file_ext in ['.doc', '.docx']:
                print(f"   📝 Word Loader: {file_path.name}")
                loader = UnstructuredWordDocumentLoader(str(file_path))
            elif file_ext == '.txt':
                print(f"   📝 Text Loader: {file_path.name}")
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                print(f"   ⚠️ Desteklenmeyen dosya türü: {file_ext}")
                return []
            
            documents = loader.load()
            
            # Metadata'yi güncelle
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "file_type": file_ext,
                    "loader_type": "langchain"
                })
            
            print(f"   ✅ {len(documents)} sayfa yüklendi (LangChain)")
            return documents
            
        except Exception as e:
            print(f"   ⚠️ LangChain yükleme hatası: {e}")
            return []
    
    def _load_document_with_unstructured(self, file_path: Path) -> List[Document]:
        """unstructured.io ile gelişmiş belge yükleme - SADECE DİĞERLERİ BAŞARISIZ OLURSA"""
        if not UNSTRUCTURED_AVAILABLE:
            return []
            
        try:
            print(f"   🧠 Unstructured.io ile deneniyor: {file_path.name}")
            
            # Unstructured için özel ayarlar - poppler sorunlarını atla
            elements = partition(
                filename=str(file_path),
                strategy="fast",  # hi_res yerine fast kullan
                pdf_infer_table_structure=False,  # Tablo çıkarımını kapat
                languages=["eng"],  # Dil belirt
            )
            
            documents = []
            for i, element in enumerate(elements):
                content = element.text.strip()
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(file_path),
                            "file_name": file_path.name,
                            "file_type": file_path.suffix,
                            "element_type": type(element).__name__,
                            "element_index": i,
                            "loader_type": "unstructured"
                        }
                    )
                    documents.append(doc)
            
            print(f"   ✅ {len(documents)} element çıkarıldı (Unstructured)")
            return documents
            
        except Exception as e:
            print(f"   ⚠️ Unstructured.io hatası: {e}")
            return []
    
    def _load_single_document(self, file_path: Path) -> List[Document]:
        """
        Tek bir belgeyi yükle
        ÖNCELIK SIRASI:
        1. PyMuPDF (PDF için en güvenilir)
        2. LangChain Loaders
        3. Unstructured.io (son çare)
        """
        print(f"📖 Yükleniyor: {file_path.name}")
        
        file_ext = file_path.suffix.lower()
        
        # PDF için önce PyMuPDF dene
        if file_ext == '.pdf' and PYMUPDF_AVAILABLE:
            documents = self._load_pdf_with_pymupdf(file_path)
            if documents:
                return documents
            print(f"   ⚠️ PyMuPDF başarısız, alternatif yöntem deneniyor...")
        
        # LangChain yükleyicileri
        if FALLBACK_LOADERS_AVAILABLE:
            documents = self._load_document_with_langchain(file_path)
            if documents:
                return documents
            print(f"   ⚠️ LangChain başarısız, son yöntem deneniyor...")
        
        # Son çare: Unstructured.io
        if UNSTRUCTURED_AVAILABLE:
            documents = self._load_document_with_unstructured(file_path)
            if documents:
                return documents
        
        print(f"   ❌ Hiçbir yöntemle yüklenemedi: {file_path.name}")
        return []
    
    def load_and_process_documents(self):
        """Tüm belgeleri yükle ve işle"""
        if not CHROMA_AVAILABLE:
            print("❌ Chroma kullanılamadığı için belge işlenemiyor")
            return False
        
        # Tüm belge dosyalarını bul
        document_files = self._get_all_document_files()
        if not document_files:
            print("❌ İşlenecek dosya bulunamadı!")
            return False
        
        print(f"📚 {len(document_files)} dosya işlenecek:")
        for i, file_path in enumerate(document_files, 1):
            print(f"  {i}. {file_path.name}")
        
        # Tüm belgeleri yükle
        all_documents = []
        successful_files = 0
        failed_files = 0
        
        for file_path in document_files:
            documents = self._load_single_document(file_path)
            if documents:
                all_documents.extend(documents)
                successful_files += 1
            else:
                failed_files += 1
        
        print(f"\n📊 Yükleme Özeti:")
        print(f"  ✅ Başarılı: {successful_files} dosya")
        print(f"  ❌ Başarısız: {failed_files} dosya")
        print(f"  📄 Toplam: {len(all_documents)} doküman elementi")
        
        if not all_documents:
            print("❌ Hiç doküman yüklenemedi!")
            return False
        
        # Metinleri böl
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(all_documents)
        print(f"✂️ {len(chunks)} metin parçası oluşturuldu")
        
        # ChromaDB ile vektör veritabanı oluştur
        print("🔧 Vektör veritabanı oluşturuluyor...")
        try:
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.vector_store_path
            )
            print("✅ Vektör veritabanı oluşturuldu!")
            return True
        except Exception as e:
            print(f"❌ Vektör veritabanı oluşturulamadı: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def search_similar(self, query, k=3):
        """Benzer dokümanları ara"""
        if not CHROMA_AVAILABLE:
            print("❌ Chroma kullanılamıyor!")
            return []
        
        # Vektör store yoksa yüklemeyi dene
        if self.vector_store is None:
            print("🔄 Vektör veritabanı yeniden yükleniyor...")
            success = self._try_load_vector_store()
            
            if not success:
                print("❌ Vektör veritabanı yüklenemedi. Belgeleri işlemeniz gerekiyor.")
                return []
        
        try:
            print(f"🔍 Arama yapılıyor: '{query}'")
            results = self.vector_store.similarity_search(query, k=k)
            print(f"✅ {len(results)} sonuç bulundu")
            return results
        except Exception as e:
            print(f"❌ Arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return []

def print_system_info():
    """Sistem bilgilerini yazdır"""
    print("=" * 60)
    print("🔍 SISTEM BİLGİLERİ")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"PyMuPDF Available: {PYMUPDF_AVAILABLE}")
    print(f"LangChain Loaders Available: {FALLBACK_LOADERS_AVAILABLE}")
    print(f"Unstructured Available: {UNSTRUCTURED_AVAILABLE}")
    print(f"Chroma Available: {CHROMA_AVAILABLE}")
    print("=" * 60)
    print()
        
def main():
    """RAG Processor test fonksiyonu"""
    print_system_info()
    
    print("🧪 RAG Processor Test Ediliyor...")
    
    # Processor'ı başlat
    processor = RAGProcessor()
    
    # Vektör veritabanı var mı kontrol et
    if processor.vector_store is None:
        print("📚 Vektör veritabanı yok, PDF'ler işleniyor...")
        success = processor.load_and_process_documents()
        if success:
            print("✅ PDF'ler başarıyla işlendi!")
        else:
            print("❌ PDF işleme başarısız!")
    else:
        print("✅ Vektör veritabanı zaten yüklü!")
    
    # Test araması yap
    print("\n🔍 Test araması yapılıyor...")
    results = processor.search_similar("organik tarım", k=2)
    print(f"📊 {len(results)} sonuç bulundu")
    
    if results:
        print("\n📄 İlk Sonuç:")
        print(f"Kaynak: {results[0].metadata.get('file_name', 'Bilinmiyor')}")
        print(f"İçerik önizleme: {results[0].page_content[:200]}...")

if __name__ == "__main__":
    main()