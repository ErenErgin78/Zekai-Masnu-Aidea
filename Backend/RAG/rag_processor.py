# rag_processor.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Modern paket
from langchain_chroma import Chroma  # Modern paket
import os
import warnings

# Uyarıları bastır
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class RAGProcessor:
    def __init__(self, pdfs_path="PDFs", vector_store_path="vector_store"):
        self.pdfs_path = pdfs_path
        self.vector_store_path = vector_store_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        
    def load_and_process_pdfs(self):
        """PDF'leri yükle ve vektör veritabanı oluştur"""
        documents = []
        
        # PDFs klasörünü kontrol et
        if not os.path.exists(self.pdfs_path):
            print(f"❌ PDFs klasörü bulunamadı: {self.pdfs_path}")
            return
        
        pdf_files = [f for f in os.listdir(self.pdfs_path) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"❌ PDFs klasöründe PDF dosyası bulunamadı: {self.pdfs_path}")
            return
            
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
            return
            
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
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.vector_store_path
        )
        print("✅ Vektör veritabanı oluşturuldu!")
        
    def search_similar(self, query, k=3):
        """Benzer dokümanları ara"""
        if self.vector_store is None:
            if not os.path.exists(self.vector_store_path):
                print("❌ Vektör veritabanı bulunamadı. Önce PDF'leri işleyin.")
                return []
                
            print("🔍 Vektör veritabanı yükleniyor...")
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
        
        results = self.vector_store.similarity_search(query, k=k)
        return results