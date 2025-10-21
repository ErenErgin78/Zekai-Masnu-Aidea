# tools/rag_tool.py
from typing import Dict, Any, List

class RAGTool:
    def __init__(self, rag_chatbot=None, max_response_length=None):
        self.name = "RAG Knowledge Tool"
        self.description = "Organik tarım bilgi bankasından bilgi getirir"
        self.rag_chatbot = rag_chatbot
        self.max_response_length = max_response_length  # None = sınırsız
    
    def query_knowledge(self, question: str) -> Dict[str, Any]:
        """RAG sisteminden bilgi al"""
        try:
            if not self.rag_chatbot:
                return {
                    "success": False,
                    "error": "RAG chatbot yüklenmemiş"
                }
            
            # RAG'den cevap al - MEVCUT query metodunu kullan
            response, sources = self.rag_chatbot.query(question)
            
            # Kaynak bilgilerini topla
            source_names = []
            if sources:
                for doc in sources:
                    source = doc.metadata.get('source', 'Bilinmeyen')
                    source_name = source.split('/')[-1].split('\\')[-1]
                    if source_name not in source_names:
                        source_names.append(source_name)
            
            return {
                "success": True,
                "query": question,
                "answer": response,
                "sources": source_names,
                "source_count": len(sources) if sources else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_summary(self, result: Dict) -> str:
        """Sonucu özetle"""
        if not result["success"]:
            return f"Hata: {result['error']}"
        
        summary = f"📚 Bilgi: {result['answer'][:200]}..."
        if result['source_count'] > 0:
            summary += f"\n   Kaynak: {', '.join(result['sources'][:3])}"
        
        return summary
    
    def __call__(self, input_text: str) -> str:
        """Tool çağrıldığında çalışacak metod"""
        result = self.query_knowledge(input_text)
        
        if result["success"]:
            answer = result["answer"]
            sources = result["sources"]
            
            # Token sınırı varsa kısalt
            if self.max_response_length and len(answer) > self.max_response_length:
                answer = answer[:self.max_response_length] + "..."
            
            response = f"📚 RAG Bilgi:\n{answer}"
            
            if sources:
                response += f"\n\n📖 Kaynaklar: {', '.join(sources[:3])}"
                if len(sources) > 3:
                    response += f" ve {len(sources) - 3} diğer kaynak"
            
            return response
        else:
            return f"❌ RAG hatası: {result['error']}"