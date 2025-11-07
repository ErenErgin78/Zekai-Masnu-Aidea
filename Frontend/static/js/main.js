// Ana class ve UI işlemleri

class UmayChat {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'default';
        this.messages = JSON.parse(localStorage.getItem('chatMessages')) || [];
        this.isTyping = false;
        this.currentChatId = this.generateChatId();
        this.charts = {}; // Grafikleri saklamak için
        
        this.init();
    }
    
    generateChatId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.applyTheme();
        this.loadMessages();
        this.setupTyping();
    }
    
    setupElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.themeToggle = document.getElementById('themeToggle');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.chatSidebar = document.getElementById('chatSidebar');
        this.weatherBtn = document.getElementById('weatherBtn');
        this.soilBtn = document.getElementById('soilBtn');
        this.weatherContent = document.getElementById('weatherContent');
        this.soilContent = document.getElementById('soilContent');
        
        // Sohbet geçmişi için alan oluştur
        this.createChatHistoryUI();
    }
    
    createChatHistoryUI() {
        // Chat listesini yükle
        this.loadChatHistory();
    }
    
    setupEventListeners() {
        // Gönder düğmesi tıklama
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter tuşu gönderir
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !this.isTyping) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Girdi değişince düğmeyi güncelle
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
        });
        
        // Tema değiştirici
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Kenar çubuğu aç/kapat
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        
        // Yeni sohbet düğmesi olayı
        const newChatBtn = document.getElementById('newChatBtn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => {
                this.startNewChat();
                this.toggleSidebar(); // Sidebar'ı kapat
            });
        }
        
        // Sidebar kapatma düğmesi olayı
        const closeSidebarBtn = document.getElementById('closeSidebarBtn');
        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', () => {
                this.toggleSidebar(); // Sidebar'ı kapat
            });
        }
        
        // Hava durumu düğmesi
        if (this.weatherBtn) {
            this.weatherBtn.addEventListener('click', () => this.loadWeatherData());
        }
        
        // Toprak analizi düğmesi
        if (this.soilBtn) {
            this.soilBtn.addEventListener('click', () => this.loadSoilData());
        }
        
        // Örnek soru butonları
        const exampleBtns = document.querySelectorAll('.example-question-btn');
        exampleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                if (question) {
                    this.messageInput.value = question;
                    this.sendMessage();
                }
            });
        });
    }
    
    setupTyping() {
        // Metin kutusunu otomatik boyutlandır
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }
    
    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isTyping;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Örnek soru butonlarını gizle
        this.hideExampleQuestions();
        
        // Kullanıcı mesajını ekle
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateSendButton();
        
        // Yazıyor göstergesini göster
        this.showTyping();
        
        // Bot cevabını API'den al ve direkt göster
        try {
            const botResponse = await getBotResponse(message);
            this.hideTyping();
            
            // Mesajı direkt göster (formatlama renderMessage içinde yapılacak)
            this.addMessage(botResponse, 'bot');
        } catch (error) {
            this.hideTyping();
            this.addMessage("Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.", 'bot');
        }
    }
    
    hideExampleQuestions() {
        const exampleQuestions = document.getElementById('exampleQuestions');
        if (exampleQuestions) {
            exampleQuestions.style.display = 'none';
        }
    }
    
    addMessage(content, sender) {
        const message = {
            content,
            sender,
            timestamp: new Date().toLocaleTimeString('tr-TR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        };
        
        this.messages.push(message);
        this.saveMessages();
        this.renderMessage(message);
    }
    
    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender}`;
        
        messageDiv.innerHTML = `
            <div class="message-bubble">${formatMessage(message.content)}</div>
            <div class="message-time">${message.timestamp}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTyping() {
        this.isTyping = true;
        
        // Girişi geçici devre dışı bırak
        this.messageInput.disabled = true;
        this.messageInput.placeholder = "UMAY düşünüyor...";
        
        // Gönder düğmesini "Durdur" yap
        this.sendButton.innerHTML = '<span class="send-icon">⏹️</span>';
        this.sendButton.title = "Durdur";
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-message';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </span>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        
        // Input'u tekrar etkinleştir
        this.messageInput.disabled = false;
        this.messageInput.placeholder = "Mesajınızı yazın...";
        
        // Send button'u normale döndür
        this.sendButton.innerHTML = '<span class="send-icon">📤</span>';
        this.sendButton.title = "Gönder";
        
        // Yazıyor göstergesini kaldır
        const typingMessage = document.getElementById('typingIndicator');
        if (typingMessage) {
            typingMessage.remove();
        }
    }
    
    loadMessages() {
        // Her zaman boş sayfa ile başla
        this.clearChat();
        this.showWelcomeMessage();
    }
    
    showWelcomeMessage() {
        // Welcome mesajı HTML'de zaten var, burada sadece kontrol ediyoruz
        const welcomeMessage = document.querySelector('.welcome-message');
        if (!welcomeMessage) {
            const div = document.createElement('div');
            div.className = 'welcome-message';
            div.innerHTML = `
                <img src="static/img/logo.png" alt="UMAY Logo" class="welcome-logo">
                <h3>Merhaba! Ben UMAY</h3>
                <p>Tarım konusunda size yardımcı olabilirim. Sorularınızı sorun!</p>
            `;
            this.chatMessages.appendChild(div);
        }
    }
    
    clearChat() {
        this.chatMessages.innerHTML = '';
        this.messages = [];
        this.currentChatId = this.generateChatId();
    }
    
    startNewChat() {
        // Mevcut chat'i kaydet
        this.saveCurrentChat();
        
        // Yeni chat başlat
        this.clearChat();
        this.showWelcomeMessage();
        
        // Örnek soruları göster
        const exampleQuestions = document.getElementById('exampleQuestions');
        if (exampleQuestions) {
            exampleQuestions.style.display = 'flex';
        }
        
        // Chat listesini güncelle (sadece UI)
        this.updateChatListUI();
    }
    
    saveCurrentChat() {
        if (this.messages.length > 0) {
            const chatData = {
                id: this.currentChatId,
                messages: [...this.messages],
                timestamp: new Date().toISOString(),
                title: this.getChatTitle()
            };
            
            // LocalStorage'a kaydet
            const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
            savedChats.push(chatData);
            localStorage.setItem('savedChats', JSON.stringify(savedChats));
        }
    }
    
    getChatTitle() {
        if (this.messages.length === 0) return 'Yeni Sohbet';
        const firstUserMessage = this.messages.find(m => m.sender === 'user');
        return firstUserMessage ? firstUserMessage.content.substring(0, 30) + '...' : 'Yeni Sohbet';
    }
    
    loadChatHistory() {
        const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
        const chatList = document.getElementById('chatList');
        
        if (!chatList) return;
        
        console.log('Loading chat history:', savedChats.length, 'chats');
        
        chatList.innerHTML = '';
        
        savedChats.reverse().forEach((chat, index) => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.dataset.chatId = chat.id;
            chatItem.style.animationDelay = `${index * 0.05}s`;
            chatItem.innerHTML = `
                <div class="chat-content">
                    <div class="chat-title">${chat.title}</div>
                    <div class="chat-time">${new Date(chat.timestamp).toLocaleString('tr-TR')}</div>
                </div>
                <button class="delete-chat-btn" data-chat-id="${chat.id}" title="Sohbeti Sil">
                    <span>🗑️</span>
                </button>
            `;
            
            chatList.appendChild(chatItem);
        });
        
        // Event listener'ı sadece bir kez ekle
        this.setupChatListEventListeners();
    }
    
    setupChatListEventListeners() {
        const chatList = document.getElementById('chatList');
        if (!chatList) return;
        
        // Eğer event listener zaten eklenmişse, tekrar ekleme
        if (chatList.hasAttribute('data-listener-added')) {
            console.log('Event listener already added, skipping...');
            return;
        }
        
        console.log('Adding event listener to chat list');
        
        // Event listener ekle
        chatList.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.delete-chat-btn');
            const chatItem = e.target.closest('.chat-item');
            
            if (deleteBtn) {
                // Delete butonuna tıklandı
                e.stopPropagation();
                e.preventDefault();
                const chatId = deleteBtn.dataset.chatId;
                console.log('Delete clicked for chat:', chatId);
                this.deleteChat(chatId);
            } else if (chatItem) {
                // Chat item'a tıklandı
                e.stopPropagation();
                e.preventDefault();
                const chatId = chatItem.dataset.chatId;
                console.log('Chat clicked:', chatId);
                const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
                const chat = savedChats.find(c => c.id === chatId);
                if (chat) {
                    this.loadChat(chat);
                }
            }
        });
        
        // Event listener eklendiğini işaretle
        chatList.setAttribute('data-listener-added', 'true');
    }
    
    loadChat(chat) {
        // Eğer aynı chat zaten yüklüyse, tekrar yükleme
        if (this.currentChatId === chat.id) {
            console.log('Same chat already loaded, skipping...');
            return;
        }
        
        console.log('Loading chat:', chat.id);
        
        // Mevcut chat'i kaydet
        this.saveCurrentChat();
        
        // Seçilen chat'i yükle
        this.messages = [...chat.messages];
        this.currentChatId = chat.id;
        
        // UI'yi güncelle
        this.chatMessages.innerHTML = '';
        this.messages.forEach(message => this.renderMessage(message));
        
        // Chat listesini güncelle (sadece UI, event listener ekleme)
        this.updateChatListUI();
        
        // Sidebar'ı kapat
        this.toggleSidebar();
    }
    
    updateChatListUI() {
        const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
        const chatList = document.getElementById('chatList');
        
        if (!chatList) return;
        
        console.log('Updating chat list UI:', savedChats.length, 'chats');
        
        chatList.innerHTML = '';
        
        savedChats.reverse().forEach((chat, index) => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.dataset.chatId = chat.id;
            chatItem.style.animationDelay = `${index * 0.05}s`;
            chatItem.innerHTML = `
                <div class="chat-content">
                    <div class="chat-title">${chat.title}</div>
                    <div class="chat-time">${new Date(chat.timestamp).toLocaleString('tr-TR')}</div>
                </div>
                <button class="delete-chat-btn" data-chat-id="${chat.id}" title="Sohbeti Sil">
                    <span>🗑️</span>
                </button>
            `;
            
            chatList.appendChild(chatItem);
        });
    }
    
    deleteChat(chatId) {
        console.log('Deleting chat:', chatId);
        
        // Onay iste
        if (confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) {
            // LocalStorage'dan sil
            const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
            console.log('Before delete:', savedChats.length, 'chats');
            
            const updatedChats = savedChats.filter(chat => chat.id !== chatId);
            console.log('After delete:', updatedChats.length, 'chats');
            
            localStorage.setItem('savedChats', JSON.stringify(updatedChats));
            
            // Eğer silinen chat aktif chat ise yeni chat başlat
            if (this.currentChatId === chatId) {
                console.log('Deleted active chat, starting new chat');
                this.startNewChat();
            } else {
                console.log('Deleted other chat, updating list');
                // Chat listesini güncelle (sadece UI)
                this.updateChatListUI();
            }
        }
    }
    
    saveMessages() {
        localStorage.setItem('chatMessages', JSON.stringify(this.messages));
    }
    
    scrollToBottom(smooth = false) {
        if (smooth) {
            this.chatMessages.scrollTo({
                top: this.chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            // Hızlı scroll - direkt pozisyon
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    toggleTheme() {
        // 3 tema arasında döngü: default -> dark -> light -> default
        const themes = ['default', 'dark', 'light'];
        const currentIndex = themes.indexOf(this.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.theme = themes[nextIndex];
        
        this.applyTheme();
        localStorage.setItem('theme', this.theme);
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        
        const themeIcon = this.themeToggle.querySelector('.theme-icon');
        // Tema ikonları
        const themeIcons = {
            'default': '🌱', // Yeşil tema
            'dark': '🌙',    // Koyu tema
            'light': '☀️'    // Açık tema
        };
        themeIcon.textContent = themeIcons[this.theme] || '🎨';
        
        // Tema tooltip'i güncelle
        const themeNames = {
            'default': 'Default (Yeşil)',
            'dark': 'Dark (Siyah)',
            'light': 'Light (Açık)'
        };
        this.themeToggle.title = `Tema: ${themeNames[this.theme] || 'Bilinmiyor'}`;
    }
    
    toggleSidebar() {
        if (this.chatSidebar) {
            this.chatSidebar.classList.toggle('open');
            // Body'ye class ekle/çıkar (toggle butonunu gizlemek için)
            document.body.classList.toggle('sidebar-open');
        }
    }
    
    // API fonksiyonlarını çağır
    async loadWeatherData() {
        await loadWeatherData(this);
    }
    
    async loadSoilData() {
        await loadSoilData(this);
    }
}

// Global instance
let umayChat;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    umayChat = new UmayChat();
});
