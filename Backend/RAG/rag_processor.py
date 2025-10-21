# rag_processor.py - DÜZELTILMIŞ
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import warnings

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
            
            print(f"🔍 Vektör veritabanı yükleniyor: {self.vector_store_path}")
            
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
        
    def load_and_process_pdfs(self):
        """PDF'leri yükle ve vektör veritabanı oluştur"""
        if not CHROMA_AVAILABLE:
            print("❌ Chroma kullanılamadığı için PDF işlenemiyor")
            return False
            
        documents = []
        
        # PDFs klasörünü kontrol et
        if not os.path.exists(self.pdfs_path):
            print(f"❌ PDFs klasörü bulunamadı: {self.pdfs_path}")
            return False
        
        pdf_files = [f for f in os.listdir(self.pdfs_path) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"❌ PDFs klasöründe PDF dosyası bulunamadı: {self.pdfs_path}")
            return False
            
        print(f"📚 {len(pdf_files)} PDF dosyası bulundu: {pdf_files}")
        
        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(self.pdfs_path, pdf_file)
                print(f"📖 İşleniyor: {pdf_file}")
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())
                print(f"✅ {pdf_file} başarıyla yüklendi")
            except Exception as e:
                print(f"❌ {pdf_file} yüklenirken hata: {e}")
        
        if not documents:
            print("❌ Hiç doküman yüklenemedi!")
            return False
            
        print(f"📄 Toplam {len(documents)} sayfa yüklendi")
        
        # Metinleri böl
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
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
                print("❌ Vektör veritabanı yüklenemedi. PDF'leri işlemeniz gerekiyor.")
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