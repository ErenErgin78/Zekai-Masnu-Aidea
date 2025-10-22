// ===== SADE VE TEMİZ CHAT UYGULAMASI =====

class AideaChat {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.messages = JSON.parse(localStorage.getItem('chatMessages')) || [];
        this.isTyping = false;
        this.currentChatId = this.generateChatId();
        
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
        
        // Chat geçmişi için container oluştur
        this.createChatHistoryUI();
    }
    
    createChatHistoryUI() {
        // Eğer sidebar zaten varsa, tekrar oluşturma
        if (document.querySelector('.chat-sidebar')) {
            return;
        }
        
        // Chat geçmişi sidebar'ı oluştur
        const sidebar = document.createElement('div');
        sidebar.className = 'chat-sidebar';
        sidebar.innerHTML = `
            <div class="chat-header-sidebar">
                <h3>💬 Sohbetler</h3>
                <button id="newChatBtn" class="new-chat-btn">+ Yeni Sohbet</button>
            </div>
            <div class="chat-list" id="chatList">
                <!-- Chat listesi buraya gelecek -->
            </div>
        `;
        
        // Ana container'a ekle
        const appContainer = document.querySelector('.app-container');
        appContainer.appendChild(sidebar);
        
        // Yeni chat butonu event listener (sadece bir kez ekle)
        const newChatBtn = document.getElementById('newChatBtn');
        if (newChatBtn && !newChatBtn.hasAttribute('data-listener-added')) {
            newChatBtn.addEventListener('click', () => {
                this.startNewChat();
            });
            newChatBtn.setAttribute('data-listener-added', 'true');
        }
        
        // Chat listesini yükle
        this.loadChatHistory();
    }
    
    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !this.isTyping) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input change
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
        });
        
        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    setupTyping() {
        // Auto-resize textarea
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
        
        // Add user message
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateSendButton();
        
        // Show typing indicator
        this.showTyping();
        
        // Get bot response from main_chatbot.py
        try {
            const botResponse = await this.getBotResponse(message);
            this.hideTyping();
            this.addMessage(botResponse, 'bot');
        } catch (error) {
            this.hideTyping();
            this.addMessage("Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.", 'bot');
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
            <div class="message-bubble">${this.formatMessage(message.content)}</div>
            <div class="message-time">${message.timestamp}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Basic formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    showTyping() {
        this.isTyping = true;
        
        // Input'u devre dışı bırak
        this.messageInput.disabled = true;
        this.messageInput.placeholder = "AIDEA düşünüyor...";
        
        // Send button'u "Durdur" olarak değiştir
        this.sendButton.innerHTML = '<span class="send-icon">⏹️</span>';
        this.sendButton.title = "Durdur";
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-message';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span>🤖</span>
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
        
        // Typing indicator'ı kaldır
        const typingMessage = document.getElementById('typingIndicator');
        if (typingMessage) {
            typingMessage.remove();
        }
    }
    
    async getBotResponse(userMessage) {
        try {
            // main_chatbot.py'ye prompt gönder
            const response = await fetch('http://localhost:8001/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: userMessage,
                    user_location: await this.getCurrentLocation()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // JSON response'dan response alanını çıkar
            let botResponse = data.response || "Cevap alınamadı.";
            
            // JSON string ise parse et
            if (typeof botResponse === 'string' && botResponse.startsWith('{')) {
                try {
                    const parsedResponse = JSON.parse(botResponse);
                    botResponse = parsedResponse.response || parsedResponse.message || botResponse;
                } catch (e) {
                    // JSON değilse olduğu gibi kullan
                }
            }
            
            // \n karakterlerini <br> ile değiştir
            botResponse = botResponse.replace(/\\n/g, '\n').replace(/\n/g, '<br>');
            
            return botResponse;
            
        } catch (error) {
            console.error('Chatbot API hatası:', error);
            return "Üzgünüm, şu anda chatbot'a bağlanamıyorum. Lütfen daha sonra tekrar deneyin.";
        }
    }
    
    async getCurrentLocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve(null);
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lon: position.coords.longitude
                    });
                },
                () => resolve(null),
                { timeout: 5000 }
            );
        });
    }
    
    loadMessages() {
        // Her zaman boş sayfa ile başla
        this.clearChat();
        this.showWelcomeMessage();
    }
    
    showWelcomeMessage() {
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'welcome-message';
        welcomeMessage.innerHTML = `
            <div class="welcome-icon">🤖</div>
            <h3>Merhaba! Ben AIDEA</h3>
            <p>Tarım konusunda size yardımcı olabilirim. Sorularınızı sorun!</p>
        `;
        this.chatMessages.appendChild(welcomeMessage);
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
        
        if (!chatList) return; // Chat list yoksa çık
        
        console.log('Loading chat history:', savedChats.length, 'chats');
        
        chatList.innerHTML = '';
        
        savedChats.reverse().forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.dataset.chatId = chat.id; // Chat ID'sini data attribute olarak ekle
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
    }
    
    updateChatListUI() {
        const savedChats = JSON.parse(localStorage.getItem('savedChats')) || [];
        const chatList = document.getElementById('chatList');
        
        if (!chatList) return;
        
        console.log('Updating chat list UI:', savedChats.length, 'chats');
        
        chatList.innerHTML = '';
        
        savedChats.reverse().forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.dataset.chatId = chat.id;
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
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        localStorage.setItem('theme', this.theme);
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        
        const themeIcon = this.themeToggle.querySelector('.theme-icon');
        themeIcon.textContent = this.theme === 'light' ? '🌙' : '☀️';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AideaChat();
});

// Add typing indicator styles
const style = document.createElement('style');
style.textContent = `
    .typing-indicator {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    
    .typing-indicator span {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--text-muted);
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
`;
document.head.appendChild(style);