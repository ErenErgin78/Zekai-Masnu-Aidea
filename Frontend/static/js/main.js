class UmayChat {
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
        
        // Hava durumu düğmesi
        if (this.weatherBtn) {
            this.weatherBtn.addEventListener('click', () => this.loadWeatherData());
        }
        
        // Toprak analizi düğmesi
        if (this.soilBtn) {
            this.soilBtn.addEventListener('click', () => this.loadSoilData());
        }
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
        
        // Kullanıcı mesajını ekle
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateSendButton();
        
        // Yazıyor göstergesini göster
        this.showTyping();
        
        // Bot cevabını API'den al
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
        // Basit biçimleme
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
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
        
        // Yazıyor göstergesini kaldır
        const typingMessage = document.getElementById('typingIndicator');
        if (typingMessage) {
            typingMessage.remove();
        }
    }
    
    async getBotResponse(userMessage) {
        try {
            // API'ye istek gönder
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
            
            // JSON içinden response alanını al
            let botResponse = data.response || "Cevap alınamadı.";
            
            // JSON metinse parse et
            if (typeof botResponse === 'string' && botResponse.startsWith('{')) {
                try {
                    const parsedResponse = JSON.parse(botResponse);
                    botResponse = parsedResponse.response || parsedResponse.message || botResponse;
                } catch (e) {
                    // JSON değilse olduğu gibi kullan
                }
            }
            
            // Satır sonlarını <br> ile değiştir
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
            <h3>Merhaba! Ben UMAY</h3>
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
        
        // Sidebar'ı kapat
        this.toggleSidebar();
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
    
    toggleSidebar() {
        if (this.chatSidebar) {
            this.chatSidebar.classList.toggle('open');
        }
    }
    
    async loadWeatherData() {
        if (!this.weatherBtn || !this.weatherContent) return;
        
        // Butonu devre dışı bırak
        this.weatherBtn.disabled = true;
        this.weatherBtn.textContent = 'Yükleniyor...';
        
        try {
            // Konum bilgisini al
            const location = await this.getCurrentLocation();
            
            // Hava API'sine istek gönder
            const response = await fetch('http://localhost:8001/weather/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: location?.lat,
                    longitude: location?.lon
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const weatherData = await response.json();
            
            // Hava panelini verilerle güncelle
            this.weatherContent.innerHTML = `
                <div class="weather-data">
                    <div class="weather-main">
                        <div class="weather-temp">${weatherData.temperature ? Math.round(weatherData.temperature) : 'N/A'}°C</div>
                        <div class="weather-desc">${weatherData.weather_code || 'N/A'}</div>
                    </div>
                    <div class="weather-details">
                        <div class="weather-item">
                            <span class="weather-label">Hissedilen Min:</span>
                            <span class="weather-value">${weatherData.apparent_temperature_min ? Math.round(weatherData.apparent_temperature_min) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Hissedilen Ort:</span>
                            <span class="weather-value">${weatherData.apparent_temperature_mean ? Math.round(weatherData.apparent_temperature_mean) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Hissedilen Max:</span>
                            <span class="weather-value">${weatherData.apparent_temperature_max ? Math.round(weatherData.apparent_temperature_max) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Yağmur:</span>
                            <span class="weather-value">${weatherData.rain_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Sağanak:</span>
                            <span class="weather-value">${weatherData.showers_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Kar:</span>
                            <span class="weather-value">${weatherData.snowfall_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Toplam Yağış:</span>
                            <span class="weather-value">${weatherData.precipitation_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Rüzgar Max:</span>
                            <span class="weather-value">${weatherData.wind_speed_max || 'N/A'} km/h</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Rüzgar Böre:</span>
                            <span class="weather-value">${weatherData.wind_gusts_max || 'N/A'} km/h</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">Güneşlenme:</span>
                            <span class="weather-value">${weatherData.sunshine_duration ? Math.round(weatherData.sunshine_duration/3600) : 'N/A'} saat</span>
                        </div>
                    </div>
                    <button class="panel-btn" onclick="this.loadWeatherData()">Yenile</button>
                </div>
            `;
            
        } catch (error) {
            console.error('Weather API hatası:', error);
            this.weatherContent.innerHTML = `
                <div class="panel-placeholder">
                    <div class="placeholder-icon">⚠️</div>
                    <p>Hava durumu bilgileri alınamadı</p>
                    <button class="panel-btn" onclick="this.loadWeatherData()">Tekrar Dene</button>
                </div>
            `;
        }
    }
    
    async loadSoilData() {
        if (!this.soilBtn || !this.soilContent) return;
        
        // Butonu devre dışı bırak
        this.soilBtn.disabled = true;
        this.soilBtn.textContent = 'Yükleniyor...';
        
        try {
            // Konum bilgisini al
            const location = await this.getCurrentLocation();
            
            // Toprak API'sine istek gönder
            const response = await fetch('http://localhost:8001/soil/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: location?.lat,
                    longitude: location?.lon
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const soilData = await response.json();
            
            // Toprak panelini verilerle güncelle
            let soilDetailsHTML = '';
            
            // Tüm özellikleri döngü ile ekle
            for (const [key, value] of Object.entries(soilData)) {
                if (key !== 'soil_type' && key !== 'soil_code' && key !== 'description' && value !== 'N/A' && value !== null) {
                    // Label'ı Türkçe'ye çevir
                    let label = key;
                    const labelMap = {
                        'pH': 'pH',
                        'Organic Carbon': 'Organik Madde',
                        'Total Nitrogen': 'Toplam Azot',
                        'C/N Ratio': 'C/N Oranı',
                        'Clay': 'Kil',
                        'Silt': 'Silt',
                        'Sand': 'Kum',
                        'Coarse Fragments': 'Kaba Parçacıklar',
                        'Bulk Density': 'Yoğunluk',
                        'Reference Bulk Density': 'Referans Yoğunluk',
                        'Root Depth': 'Kök Derinliği',
                        'Available Water Capacity': 'Su Kapasitesi',
                        'Cation Exchange Capacity': 'Katyon Değişim Kapasitesi',
                        'Clay CEC': 'Kil CEC',
                        'Effective CEC': 'Etkili CEC',
                        'Total Exchangeable Bases': 'Toplam Değişebilir Bazlar',
                        'Base Saturation': 'Baz Doygunluğu',
                        'Exchangeable Sodium Percentage': 'Değişebilir Sodyum Yüzdesi',
                        'Aluminum Saturation': 'Alüminyum Doygunluğu',
                        'Electrical Conductivity': 'Elektriksel İletkenlik',
                        'Total Carbon Equivalent': 'Toplam Karbon Eşdeğeri',
                        'Gypsum Content': 'Jips İçeriği'
                    };
                    
                    label = labelMap[key] || key;
                    
                    soilDetailsHTML += `
                        <div class="soil-item">
                            <span class="soil-label">${label}:</span>
                            <span class="soil-value">${value}</span>
                        </div>
                    `;
                }
            }
            
            this.soilContent.innerHTML = `
                <div class="soil-data">
                    <div class="soil-main">
                        <div class="soil-type">${soilData.soil_type || 'Bilinmiyor'}</div>
                        <div class="soil-desc">${soilData.description || 'Toprak analizi yapılamadı'}</div>
                    </div>
                    <div class="soil-details">
                        ${soilDetailsHTML}
                    </div>
                    <button class="panel-btn" onclick="this.loadSoilData()">Yenile</button>
                </div>
            `;
            
        } catch (error) {
            console.error('Soil API hatası:', error);
            this.soilContent.innerHTML = `
                <div class="panel-placeholder">
                    <div class="placeholder-icon">⚠️</div>
                    <p>Toprak analizi bilgileri alınamadı</p>
                    <button class="panel-btn" onclick="this.loadSoilData()">Tekrar Dene</button>
                </div>
            `;
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UmayChat();
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