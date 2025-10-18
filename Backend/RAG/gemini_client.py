# gemini_client.py
import sys
import os

# En başta, import'lardan ÖNCE uyarıları kapat
os.environ['GRPC_VERBOSITY'] = 'NONE'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'

# stderr'i geçici olarak kapat (ALTS uyarısı için)
class SuppressStderr:
    def __enter__(self):
        self.original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, *args):
        sys.stderr.close()
        sys.stderr = self.original_stderr

# Google kütüphanelerini sessizce import et
with SuppressStderr():
    import google.generativeai as genai

from dotenv import load_dotenv
import warnings
import logging

# Tüm uyarıları kapat
warnings.filterwarnings('ignore')
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('google').setLevel(logging.CRITICAL)
logging.getLogger('grpc').setLevel(logging.CRITICAL)
logging.getLogger('absl').setLevel(logging.CRITICAL)

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY bulunamadı. .env dosyasını kontrol edin.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✅ Gemini client başlatıldı")
    
    def generate_response(self, prompt, context=""):
        full_prompt = f"""
Sen organik tarım konusunda uzman, yardımcı ve samimi bir asistansın.

📚 BAĞLAM (Sana sağlanan kaynaklardan):
{context}

❓ KULLANICI SORUSU:
{prompt}

📝 GÖREVIN:
1. Yukarıdaki BAĞLAM bilgilerine dayanarak soruyu yanıtla
2. Cevabını açık, anlaşılır ve sohbet eder bir dille yaz
3. Mümkünse pratik örnekler ve öneriler ekle
4. Bağlamda eksik veya belirsiz bilgiler varsa, kullanıcıya şu formatta araştırma önerileri sun:

CEVAP FORMATI:

EĞER BAĞLAMDA YETERLİ BİLGİ VARSA:
---
[Soruya detaylı ve samimi cevap]

💡 İPUCU: [Pratik bir öneri veya ek bilgi]

🔍 DAHA FAZLA ARAŞTIRMA İÇİN:
• [İlgili konu 1]
• [İlgili konu 2]
---

EĞER BAĞLAMDA YETERLİ BİLGİ YOKSA:
---
Elimdeki kaynaklarda bu konuyla ilgili detaylı bilgi bulamadım, ama sana yardımcı olmak için:

📌 GENEL BİLGİ:
[Varsa genel bilgiler]

🔍 ARAŞTIRMA ÖNERİLERİ:
Şu konularda daha fazla bilgi edinmeni öneririm:
• [Önerilen araştırma konusu 1]
• [Önerilen araştırma konusu 2]
• [Önerilen araştırma konusu 3]

💬 Daha spesifik bir soru sorabilir veya farklı bir açıdan sorabilirim!
---

KURALLAR:
✅ Samimi ve yardımcı ol
✅ Teknik terimleri açıkla
✅ Pratik örnekler ver
✅ Bağlamdaki bilgileri kaynak göster ("Kaynaklara göre...")
❌ Bağlamda olmayan bilgileri uydurmama
❌ "Bağlam" kelimesini kullanıcıya gösterme, doğal konuş
        """
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini hatası: {e}"