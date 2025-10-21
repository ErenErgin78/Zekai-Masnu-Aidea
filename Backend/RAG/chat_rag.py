# chat_rag.py - Token Optimizasyonlu
from rag_processor import RAGProcessor
from gemini_client import GeminiClient
import os
import warnings

warnings.filterwarnings('ignore')

class RAGChatbot:
    def __init__(self, max_sources=3, max_context_length=3000):
        print("🤖 RAG Chatbot başlatılıyor...")
        self.rag_processor = RAGProcessor()
        self.gemini_client = GeminiClient()
        self.conversation_history = []
        self.max_sources = max_sources  # Token tasarrufu için
        self.max_context_length = max_context_length  # Context token limiti
        print("✅ RAG Chatbot hazır!")
    
    def query(self, question: str, num_sources: int = None):
        """Soru sor ve cevap al
        
        Args:
            question: Kullanıcı sorusu
            num_sources: Kaç kaynak kullanılacak (None ise default kullanılır)
        """
        print(f"\n📝 Soru: {question}")
        
        # Kaynak sayısını belirle
        k = num_sources if num_sources is not None else self.max_sources
        
        # Benzer içerikleri bul
        similar_docs = self.rag_processor.search_similar(question, k=k)
        
        if not similar_docs:
            print("⚠️ İlgili içerik bulunamadı")
            return "Üzgünüm, bu konuyla ilgili kaynaklarımda yeterli bilgi bulamadım. Lütfen başka bir şekilde sormayı deneyin veya farklı bir konu hakkında soru sorun.", []
        
        print(f"✅ {len(similar_docs)} kaynak bulundu")
        
        # Context oluştur - token limiti ile
        context_parts = []
        current_length = 0
        
        for doc in similar_docs:
            content = doc.page_content
            content_length = len(content)
            
            # Token limiti kontrolü (yaklaşık: 1 token ≈ 4 karakter)
            if current_length + content_length > self.max_context_length:
                # Kalan alanı kullan
                remaining = self.max_context_length - current_length
                if remaining > 100:  # En az 100 karakter ekle
                    context_parts.append(content[:remaining])
                break
            
            context_parts.append(content)
            current_length += content_length
        
        context = "\n\n".join(context_parts)
        
        print(f"📊 Context uzunluğu: {len(context)} karakter (~{len(context)//4} token)")
        
        # Gemini'ye sor
        print("🤔 Gemini cevap üretiyor...")
        response = self.gemini_client.generate_response(question, context)
        
        # Konuşma geçmişine ekle
        self.conversation_history.append({
            "soru": question,
            "cevap": response,
            "kaynak_sayisi": len(similar_docs)
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
    """Vektör veritabanını kontrol et"""
    vector_store_path = "vector_store"
    sqlite_file = os.path.join(vector_store_path, "chroma.sqlite3")
    
    if os.path.exists(sqlite_file):
        print(f"✅ Vektör veritabanı bulundu: {sqlite_file}")
        return True
    else:
        print(f"❌ Vektör veritabanı bulunamadı: {sqlite_file}")
        return False

def main():
    print("=" * 60)
    print("🌱 ORGANİK TARIM ASISTANI 🌱".center(60))
    print("=" * 60)
    print()
    
    # Vektör veritabanını kontrol et
    if not setup_vector_store():
        print("\n🔥 PDF'ler işleniyor, lütfen bekleyin...")
        rag_processor = RAGProcessor()
        success = rag_processor.load_and_process_pdfs()
        if success:
            print("✅ İşlem tamamlandı!")
        else:
            print("❌ PDF işleme başarısız! RAG devre dışı.")
            return
    
    # Chatbot'u başlat (token optimizasyonlu)
    chatbot = RAGChatbot(max_sources=3, max_context_length=3000)
    
    print("\n💬 Merhaba! Organik tarım hakkındaki sorularını cevaplayabilirim.")
    print("🔍 İpucu: 'çıkış', 'exit' veya 'quit' yazarak çıkabilirsin.\n")
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
            response, sources = chatbot.query(user_input)
            print(f"\n🤖 Asistan:\n{response}")
            
            # Kaynakları göster
            chatbot.show_sources(sources)
            
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere! İyi günler!")
            break
        except Exception as e:
            print(f"\n❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()
            print("Lütfen tekrar deneyin.")
    
    # Konuşma özeti
    if chatbot.conversation_history:
        print("\n" + "=" * 60)
        print(f"📊 Toplam {len(chatbot.conversation_history)} soru cevaplandı.")
        print("=" * 60)

if __name__ == "__main__":
    main()