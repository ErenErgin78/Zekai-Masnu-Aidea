# chat_rag.py
from rag_processor import RAGProcessor
from gemini_client import GeminiClient
import os
import shutil
import time
import warnings

warnings.filterwarnings('ignore')

class RAGChatbot:
    def __init__(self):
        self.rag_processor = RAGProcessor()
        self.gemini_client = GeminiClient()
        self.conversation_history = []
    
    def query(self, question):
        # Benzer içerikleri bul
        similar_docs = self.rag_processor.search_similar(question, k=5)
        
        if not similar_docs:
            return "❌ İlgili içerik bulunamadı. Lütfen daha farklı bir soru deneyin.", []
            
        context = "\n".join([doc.page_content for doc in similar_docs])
        
        # Gemini'ye sor
        response = self.gemini_client.generate_response(question, context)
        
        # Konuşma geçmişine ekle
        self.conversation_history.append({
            "soru": question,
            "cevap": response
        })
        
        return response, similar_docs
    
    def show_sources(self, sources):
        """Kaynakları göster (tekrarsız + chunk sayısı)"""
        if sources:
            # Kaynak isimlerine göre chunk sayısını say
            source_counts = {}
            for doc in sources:
                source = doc.metadata.get('source', 'Bilinmeyen')
                source_name = os.path.basename(source)
                source_counts[source_name] = source_counts.get(source_name, 0) + 1
            
            print("\n📚 KAYNAKLAR:")
            for i, (source_name, count) in enumerate(source_counts.items(), 1):
                if count > 1:
                    print(f"  {i}. {source_name} ({count} bölüm)")
                else:
                    print(f"  {i}. {source_name}")

def setup_vector_store():
    """Vektör veritabanını kontrol et ve gerekirse oluştur"""
    vector_store_path = "vector_store"
    
    if os.path.exists(vector_store_path):
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings
            
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            temp_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)
            doc_count = temp_store._collection.count()
            
            del temp_store
            time.sleep(0.5)
            
            if doc_count > 0:
                print(f"✅ Vektör veritabanı hazır ({doc_count} doküman)")
                return True
            else:
                print("⚠️ Vektör veritabanı boş!")
                return False
        except Exception as e:
            print(f"⚠️ Vektör veritabanı hatası: {e}")
            return False
    else:
        print("❌ Vektör veritabanı bulunamadı!")
        return False

def main():
    print("=" * 60)
    print("🌱 ORGANİK TARIM ASISTANI 🌱".center(60))
    print("=" * 60)
    print()
    
    # Vektör veritabanını kontrol et
    if not setup_vector_store():
        print("\n📥 PDF'ler işleniyor, lütfen bekleyin...")
        rag_processor = RAGProcessor()
        rag_processor.load_and_process_pdfs()
        print("✅ İşlem tamamlandı!")
    
    # Chatbot'u başlat
    chatbot = RAGChatbot()
    
    print("\n💬 Merhaba! Organik tarım hakkında sorularını cevaplayabilirim.")
    print("📝 İpucu: 'çıkış', 'exit' veya 'quit' yazarak çıkabilirsin.\n")
    print("=" * 60)
    
    while True:
        try:
            # Kullanıcıdan soru al
            print("\n" + "─" * 60)
            user_input = input("🙋 Sen: ").strip()
            
            # Çıkış kontrolü
            if user_input.lower() in ['çıkış', 'exit', 'quit', 'q', 'bye']:
                print("\n👋 Görüşmek üzere! İyi günler!")
                break
            
            # Boş input kontrolü
            if not user_input:
                print("⚠️ Lütfen bir soru yazın.")
                continue
            
            # Cevap al
            print("\n💭 Düşünüyorum...", end="\r")
            response, sources = chatbot.query(user_input)
            print(" " * 50, end="\r")  # Temizle
            print(f"\n🤖 Asistan:\n{response}")
            
            # Kaynakları göster
            chatbot.show_sources(sources)
            
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere! İyi günler!")
            break
        except Exception as e:
            print(f"\n❌ Bir hata oluştu: {e}")
            print("Lütfen tekrar deneyin.")
    
    # Konuşma özeti
    if chatbot.conversation_history:
        print("\n" + "=" * 60)
        print(f"📊 Toplam {len(chatbot.conversation_history)} soru cevaplandı.")
        print("=" * 60)

if __name__ == "__main__":
    main()