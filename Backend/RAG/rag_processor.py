# rag_processor_improved.py - AKILLI PDF YÖNETİMİ (TOKEN BAZLI)
import os
import sys
import warnings
from pathlib import Path
from typing import List, Set, Dict, Optional

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# Tokenizer için
try:
    from transformers import AutoTokenizer
    TOKENIZER_AVAILABLE = True
except ImportError:
    TOKENIZER_AVAILABLE = False
    print("⚠️ Transformers kütüphanesi kullanılamıyor")

# PDF Fallback yükleyiciler
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

# PyMuPDF
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF kullanılamıyor")

# Unstructured
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
    def __init__(self, pdfs_path="PDFs", vector_store_path="vector_store", model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        self.pdfs_path = pdfs_path
        self.vector_store_path = vector_store_path
        self.model_name = model_name
        
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB kütüphanesi yüklenemedi!")
            
        print("🔧 MULTILINGUAL Embeddings modeli yükleniyor...")  # 🎯 MODEL İSMİ
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ MULTILINGUAL Embeddings hazır!")  # 🎯 MODEL İSMİ
        
        # Tokenizer'ı yükle (token bazlı bölme için)
        self.tokenizer = None
        if TOKENIZER_AVAILABLE:
            try:
                print("🔧 MULTILINGUAL Tokenizer yükleniyor...")  # 🎯 MODEL İSMİ
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                # 🎯 TOKEN LİMİT BİLGİSİ EKLE
                model_max_length = self.tokenizer.model_max_length
                print(f"🎉 MULTILINGUAL Token Limit: {model_max_length}")
                
                print("✅ Tokenizer hazır")
            except Exception as e:
                print(f"⚠️ Tokenizer yüklenemedi: {e}")
                self.tokenizer = None
        
        self.vector_store = None
        
        # Başlangıçta vektör veritabanını yükle
        self._try_load_vector_store()
    
    def _create_token_text_splitter(self):
        """MULTILINGUAL için token bazlı text splitter"""
        if self.tokenizer and TOKENIZER_AVAILABLE:
            try:
                # Modelin token limitine göre güvenli chunk size
                return TokenTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=150
                )
            except Exception as e:
                print(f"⚠️ Token splitter oluşturulamadı: {e}")
        
        # Fallback: karakter bazlı ama daha küçük chunk'lar
        print("⚠️ Tokenizer yok, karakter bazlı bölme kullanılıyor")
        return RecursiveCharacterTextSplitter(
            chunk_size=3000,  # Daha küçük - token sınırına uyması için
            chunk_overlap=300
        )
    
    def _count_tokens(self, text: str) -> int:
        """Metnin token sayısını hesapla"""
        if self.tokenizer and text:
            return len(self.tokenizer.encode(text))
        return len(text) // 4  # Tahmini: 1 token ≈ 4 karakter
    
    def _try_load_vector_store(self):
        """Vektör veritabanını yüklemeyi dene"""
        try:
            if not os.path.exists(self.vector_store_path):
                print(f"⚠️ Vektör klasörü bulunamadı: {self.vector_store_path}")
                return False
            
            sqlite_file = os.path.join(self.vector_store_path, "chroma.sqlite3")
            if not os.path.exists(sqlite_file):
                print(f"⚠️ chroma.sqlite3 bulunamadı: {sqlite_file}")
                return False
            
            print(f"📂 Vektör veritabanı yükleniyor: {self.vector_store_path}")
            
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
            
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
    
    def _get_files_in_vector_store(self) -> Set[str]:
        """
        Vektör store'daki tüm dosyaların tam yollarını çıkar
        """
        if self.vector_store is None:
            print("⚠️ Vektör store yüklü değil")
            return set()
        
        try:
            print("🔍 Vektör store'daki dosyalar sorgulanıyor...")
            
            collection = self.vector_store._collection
            all_data = collection.get(include=['metadatas'])
            
            files_in_store = set()
            if all_data and 'metadatas' in all_data:
                for metadata in all_data['metadatas']:
                    if metadata and 'source' in metadata:
                        source_path = Path(metadata['source']).resolve()
                        files_in_store.add(str(source_path))
            
            print(f"✅ Vektör store'da {len(files_in_store)} dosya bulundu")
            return files_in_store
            
        except Exception as e:
            print(f"❌ Vektör store sorgu hatası: {e}")
            import traceback
            traceback.print_exc()
            return set()
    
    def _delete_documents_by_source(self, file_path: str):
        """
        Belirli bir kaynak dosyaya ait tüm chunk'ları vektör store'dan sil
        """
        if self.vector_store is None:
            print("⚠️ Vektör store yüklü değil")
            return False
        
        try:
            print(f"🗑️  Siliniyor: {Path(file_path).name}")
            
            collection = self.vector_store._collection
            
            all_data = collection.get(include=['metadatas'])
            ids_to_delete = []
            
            if all_data and 'ids' in all_data and 'metadatas' in all_data:
                for idx, metadata in enumerate(all_data['metadatas']):
                    if metadata and 'source' in metadata:
                        meta_source = str(Path(metadata['source']).resolve())
                        target_source = str(Path(file_path).resolve())
                        
                        if meta_source == target_source:
                            ids_to_delete.append(all_data['ids'][idx])
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                print(f"   ✅ {len(ids_to_delete)} chunk silindi")
                return True
            else:
                print(f"   ⚠️ Silinecek chunk bulunamadı")
                return False
                
        except Exception as e:
            print(f"   ❌ Silme hatası: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_all_document_files(self) -> List[Path]:
        """PDFs klasörü ve tüm alt klasörlerindeki desteklenen dosyaları bul"""
        pdfs_path = Path(self.pdfs_path)
        
        if not pdfs_path.exists():
            print(f"❌ PDFs klasörü bulunamadı: {self.pdfs_path}")
            return []
        
        supported_extensions = {
            '.pdf', '.doc', '.docx', '.txt', 
            '.rtf', '.odt', '.pptx', '.ppt'
        }
        
        document_files = []
        for ext in supported_extensions:
            files = list(pdfs_path.rglob(f"*{ext}"))
            document_files.extend(files)
        
        document_files = [f.resolve() for f in set(document_files)]
        document_files.sort()
        
        print(f"🔍 Tarama tamamlandı. {len(document_files)} dosya bulundu.")
        return document_files
    
    def _load_pdf_with_pymupdf(self, file_path: Path) -> List[Document]:
        """PyMuPDF ile PDF yükleme"""
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
                            "loader_type": "pymupdf",
                            "token_count": self._count_tokens(text)  # Token sayısını ekle
                        }
                    )
                    documents.append(document)
            
            doc.close()
            
            if documents:
                total_tokens = sum(doc.metadata.get('token_count', 0) for doc in documents)
                print(f"   ✅ {len(documents)} sayfa yüklendi (PyMuPDF) - Toplam ~{total_tokens} token")
            else:
                print(f"   ⚠️ PDF açıldı ama metin çıkarılamadı")
            
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
            
            non_empty_docs = []
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "file_type": file_ext,
                    "loader_type": "langchain",
                    "token_count": self._count_tokens(doc.page_content)  # Token sayısını ekle
                })
                
                if doc.page_content and doc.page_content.strip():
                    non_empty_docs.append(doc)
            
            if non_empty_docs:
                total_tokens = sum(doc.metadata.get('token_count', 0) for doc in non_empty_docs)
                print(f"   ✅ {len(non_empty_docs)} sayfa yüklendi (LangChain) - Toplam ~{total_tokens} token")
            else:
                print(f"   ⚠️ Dosya yüklendi ama içerik boş")
            
            return non_empty_docs
            
        except Exception as e:
            print(f"   ⚠️ LangChain yükleme hatası: {e}")
            return []
    
    def _load_document_with_unstructured(self, file_path: Path) -> List[Document]:
        """unstructured.io ile gelişmiş belge yükleme"""
        if not UNSTRUCTURED_AVAILABLE:
            return []
            
        try:
            print(f"   🧠 Unstructured.io ile deneniyor: {file_path.name}")
            
            elements = partition(
                filename=str(file_path),
                strategy="fast",
                pdf_infer_table_structure=False,
                languages=["eng"],
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
                            "loader_type": "unstructured",
                            "token_count": self._count_tokens(content)  # Token sayısını ekle
                        }
                    )
                    documents.append(doc)
            
            if documents:
                total_tokens = sum(doc.metadata.get('token_count', 0) for doc in documents)
                print(f"   ✅ {len(documents)} element çıkarıldı (Unstructured) - Toplam ~{total_tokens} token")
            return documents
            
        except Exception as e:
            print(f"   ⚠️ Unstructured.io hatası: {e}")
            return []
    
    def _load_single_document(self, file_path: Path) -> List[Document]:
        """Tek bir belgeyi yükle"""
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
    
    def load_and_process_documents(self, force_reprocess=False):
        """
        Tüm belgeleri akıllı şekilde yükle ve işle (TOKEN BAZLI)
        """
        if not CHROMA_AVAILABLE:
            print("❌ Chroma kullanılamadığı için belge işlenemiyor")
            return False
        
        print("\n" + "="*70)
        print("🚀 MULTILINGUAL AKILLI PDF YÖNETİMİ BAŞLATILIYOR (TOKEN BAZLI)")
        print("="*70)
        
        # 1. PDFs klasöründeki mevcut dosyaları bul
        current_files = self._get_all_document_files()
        if not current_files:
            print("❌ İşlenecek dosya bulunamadı!")
            return False
        
        current_files_set = {str(f) for f in current_files}
        print(f"📂 PDFs klasöründe {len(current_files_set)} dosya bulundu")
        
        # 2. Vektör store'daki dosyaları bul
        files_in_store = set()
        if self.vector_store is not None and not force_reprocess:
            files_in_store = self._get_files_in_vector_store()
        else:
            if force_reprocess:
                print("⚠️ FORCE_REPROCESS aktif - Tüm dosyalar yeniden işlenecek")
            else:
                print("⚠️ Vektör store bulunamadı - Tüm dosyalar işlenecek")
        
        # 3. Farkları hesapla
        new_files = current_files_set - files_in_store
        deleted_files = files_in_store - current_files_set
        existing_files = current_files_set & files_in_store
        
        print("\n" + "="*70)
        print("📊 DURUM ANALİZİ")
        print("="*70)
        print(f"✅ Zaten işlenmiş: {len(existing_files)} dosya")
        print(f"🆕 Yeni eklenen: {len(new_files)} dosya")
        print(f"🗑️  Silinen: {len(deleted_files)} dosya")
        print("="*70)
        
        # 4. Silinen dosyaları vektör store'dan temizle
        if deleted_files:
            print(f"\n🗑️  Silinen {len(deleted_files)} dosya vektör store'dan kaldırılıyor...")
            deleted_count = 0
            for deleted_file in deleted_files:
                if self._delete_documents_by_source(deleted_file):
                    deleted_count += 1
            print(f"✅ {deleted_count} dosya başarıyla temizlendi")
        
        # 5. Yeni dosyaları işle
        if not new_files:
            print("\n✅ Tüm dosyalar güncel! İşlenecek yeni dosya yok.")
            return True
        
        print(f"\n🆕 {len(new_files)} yeni dosya işlenecek:")
        new_files_list = [Path(f) for f in sorted(new_files)]
        for i, file_path in enumerate(new_files_list, 1):
            print(f"  {i}. {file_path.name}")
        
        # 6. Yeni dosyaları yükle
        all_documents = []
        successful_files = 0
        failed_files = 0
        empty_content_files = []
        
        print("\n📖 Dosyalar yükleniyor...")
        for file_path in new_files_list:
            documents = self._load_single_document(file_path)
            if documents:
                all_documents.extend(documents)
                successful_files += 1
            else:
                failed_files += 1
                empty_content_files.append(file_path.name)
        
        print(f"\n📊 Yükleme Özeti:")
        print(f"  ✅ Başarılı: {successful_files} dosya")
        print(f"  ❌ Başarısız: {failed_files} dosya")
        print(f"  📄 Toplam: {len(all_documents)} doküman elementi")
        
        if empty_content_files:
            print(f"\n⚠️ İçerik Çıkarılamayan Dosyalar ({len(empty_content_files)}):")
            for file_name in empty_content_files[:10]:
                print(f"   - {file_name}")
            if len(empty_content_files) > 10:
                print(f"   ... ve {len(empty_content_files) - 10} dosya daha")
            print("\n💡 Bu dosyalar muhtemelen taranmış görüntü (OCR gerekli)")
        
        if not all_documents:
            print("⚠️ Yeni yüklenecek doküman yok")
            return True
        
        # 7. TOKEN BAZLI METİN BÖLME
        print("\n✂️  TOKEN BAZLI metin bölme yapılıyor...")
        text_splitter = self._create_token_text_splitter()
        chunks = text_splitter.split_documents(all_documents)
        
        # Token istatistiklerini hesapla
        total_tokens = sum(self._count_tokens(chunk.page_content) for chunk in chunks)
        avg_tokens = total_tokens // len(chunks) if chunks else 0
        
        print(f"✂️  {len(chunks)} metin parçası oluşturuldu")
        print(f"📊 Token istatistikleri: Toplam ~{total_tokens} token, Ortalama ~{avg_tokens} token/parça")
        
        # Chunk boyutu analizi
        chunk_sizes = [self._count_tokens(chunk.page_content) for chunk in chunks]
        max_tokens = max(chunk_sizes) if chunk_sizes else 0
        min_tokens = min(chunk_sizes) if chunk_sizes else 0
        
        print(f"📏 Chunk boyutları: Min {min_tokens}, Maks {max_tokens} token")
        
        if max_tokens > 1900:
            print("⚠️ UYARI: Bazı chunk'lar 1900 token sınırına yaklaşıyor!")
        elif max_tokens > 1500:
            print("✅ Chunk boyutları optimum aralıkta")
        
        # Boş chunk kontrolü
        if len(chunks) == 0:
            print("⚠️ UYARI: Hiç metin parçası oluşturulamadı!")
            print("✅ Silme işlemi tamamlandı ama yeni ekleme yapılamadı")
            return True
        
        # 8. Vektör store'a ekle
        print("🔧 Yeni dokümanlar vektör veritabanına ekleniyor...")
        try:
            if self.vector_store is None:
                self.vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=self.vector_store_path
                )
                print("✅ Vektör veritabanı oluşturuldu!")
            else:
                self.vector_store.add_documents(chunks)
                print("✅ Yeni dokümanlar eklendi!")
            
            print("\n" + "="*70)
            print("🎉 TOKEN BAZLI İŞLEM TAMAMLANDI")
            print("="*70)
            return True
            
        except Exception as e:
            print(f"❌ Vektör veritabanı işlemi başarısız: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def search_similar(self, query, k=3):
        """Benzer dokümanları ara"""
        if not CHROMA_AVAILABLE:
            print("❌ Chroma kullanılamıyor!")
            return []
        
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
    
    def get_vector_store_stats(self):
        """Vektör store istatistiklerini göster"""
        if self.vector_store is None:
            print("⚠️ Vektör store yüklü değil")
            return
        
        try:
            files_in_store = self._get_files_in_vector_store()
            
            print("\n" + "="*70)
            print("📊 VEKTÖR STORE İSTATİSTİKLERİ")
            print("="*70)
            print(f"Toplam dosya sayısı: {len(files_in_store)}")
            print("\nDosyalar:")
            for i, file_path in enumerate(sorted(files_in_store), 1):
                print(f"  {i}. {Path(file_path).name}")
            print("="*70)
            
        except Exception as e:
            print(f"❌ İstatistik hatası: {e}")

def print_system_info():
    """Sistem bilgilerini yazdır"""
    print("=" * 70)
    print("🔍 SISTEM BİLGİLERİ")
    print("=" * 70)
    print(f"Python Version: {sys.version}")
    print(f"PyMuPDF Available: {PYMUPDF_AVAILABLE}")
    print(f"LangChain Loaders Available: {FALLBACK_LOADERS_AVAILABLE}")
    print(f"Unstructured Available: {UNSTRUCTURED_AVAILABLE}")
    print(f"Chroma Available: {CHROMA_AVAILABLE}")
    print(f"Tokenizer Available: {TOKENIZER_AVAILABLE}")
    print("=" * 70)
    print()

def main():
    """RAG Processor test fonksiyonu"""
    print_system_info()
    
    print("🧪 MULTILINGUAL AKILLI RAG PROCESSOR TEST EDİLİYOR... (TOKEN BAZLI)")
    print()
    
    # Processor'ı başlat
    processor = RAGProcessor()

    # 🎯 MODEL BİLGİSİNİ GÖSTER
    print(f"🔧 Kullanılan Model: {processor.model_name}")
    if processor.tokenizer:
        print(f"🔧 Token Limit: {processor.tokenizer.model_max_length}")
    print()
    
    # Vektör store istatistiklerini göster
    if processor.vector_store is not None:
        processor.get_vector_store_stats()
    
    # Akıllı işleme - sadece yeni dosyaları işle
    print("\n📚 Akıllı PDF işleme başlatılıyor...")
    success = processor.load_and_process_documents(force_reprocess=False)
    
    if success:
        print("\n✅ İşlem başarıyla tamamlandı!")
        
        # Güncel istatistikleri göster
        processor.get_vector_store_stats()
        
        # Test araması yap
        print("\n🔍 Test araması yapılıyor...")
        results = processor.search_similar("organik tarım", k=2)
        
        if results:
            print("\n📄 İlk Sonuç:")
            print(f"Kaynak: {results[0].metadata.get('file_name', 'Bilinmiyor')}")
            content_preview = results[0].page_content[:200]
            token_count = processor._count_tokens(results[0].page_content)
            print(f"Token sayısı: {token_count}")
            print(f"İçerik önizleme: {content_preview}...")
    else:
        print("\n❌ İşlem başarısız!")

if __name__ == "__main__":
    main()