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
            const botResponse = await this.getBotResponse(message);
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
            <div class="message-bubble">${this.formatMessage(message.content)}</div>
            <div class="message-time">${message.timestamp}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Basit biçimleme - önce markdown formatlamasını yap
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Formatlamadan sonra kalan ham markdown etiketlerini temizle
        // HTML etiketleri içindeki * karakterlerini korumak için önce HTML etiketlerini placeholder'a çevir
        const htmlTagPlaceholders = {};
        let placeholderIndex = 0;
        
        // HTML etiketlerini placeholder'a çevir
        formatted = formatted.replace(/<[^>]+>/g, (match) => {
            const placeholder = `__HTMLPLACEHOLDER_${placeholderIndex}__`;
            htmlTagPlaceholders[placeholder] = match;
            placeholderIndex++;
            return placeholder;
        });
        
        // Kalan ** ve * karakterlerini temizle
        formatted = formatted.replace(/\*\*/g, ''); // Kalan ** karakterlerini kaldır
        formatted = formatted.replace(/\*/g, ''); // Kalan * karakterlerini kaldır
        
        // Placeholder'ları geri çevir
        for (const [placeholder, htmlTag] of Object.entries(htmlTagPlaceholders)) {
            formatted = formatted.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), htmlTag);
        }
        
        // Eşleşmeyen/bozuk HTML etiketlerini temizle
        formatted = this.cleanMismatchedHtmlTags(formatted);
        
        return formatted;
    }
    
    cleanMismatchedHtmlTags(html) {
        // Eşleşmeyen HTML etiketlerini temizle
        // Önce tüm etiketleri ve pozisyonlarını bul
        const tagStack = [];
        const tags = [];
        const tagRegex = /<\/?([a-zA-Z][a-zA-Z0-9]*)[^>]*>/g;
        let match;
        
        // Tüm etiketleri topla
        while ((match = tagRegex.exec(html)) !== null) {
            tags.push({
                fullTag: match[0],
                tagName: match[1].toLowerCase(),
                index: match.index,
                isClosing: match[0].startsWith('</'),
                isSelfClosing: match[0].endsWith('/>') || match[1].toLowerCase() === 'br' || match[1].toLowerCase() === 'img' || match[1].toLowerCase() === 'hr'
            });
        }
        
        // Eşleşmeyen etiketleri bul
        const tagsToRemove = [];
        
        for (let i = 0; i < tags.length; i++) {
            const tag = tags[i];
            
            if (tag.isClosing) {
                // Kapanış etiketi - eşleşen açılış etiketi var mı kontrol et
                const lastOpenIndex = tagStack.lastIndexOf(tag.tagName);
                if (lastOpenIndex !== -1) {
                    // Eşleşen açılış etiketi var - stack'ten kaldır
                    tagStack.splice(lastOpenIndex, 1);
                } else {
                    // Eşleşmeyen kapanış etiketi - kaldırılacak
                    tagsToRemove.push(tag);
                }
            } else if (!tag.isSelfClosing) {
                // Açılış etiketi (self-closing değil) - stack'e ekle
                tagStack.push(tag.tagName);
            }
        }
        
        // Eşleşmeyen etiketleri kaldır (ters sırada - son indexten başa)
        tagsToRemove.sort((a, b) => b.index - a.index);
        for (const tag of tagsToRemove) {
            html = html.substring(0, tag.index) + html.substring(tag.index + tag.fullTag.length);
        }
        
        return html;
    }
    
    cleanBrokenHtmlTags(html) {
        // Bozuk HTML yapılarını temizle
        // Örnek: <br><br></em>, <br></strong>, vb.
        
        // 1. Self-closing etiketlerden sonra gelen eşleşmeyen kapanış etiketlerini temizle
        // Örnek: <br></em>, <br></strong>, <br><br></em>
        html = html.replace(/(<(?:br|img|hr|input)[^>]*>)\s*<\/[^>]+>/gi, '$1');
        
        // 2. Ardışık <br> etiketlerini normalize et (maksimum 2'ye indir)
        html = html.replace(/(<br[^>]*>\s*){3,}/gi, '<br><br>');
        
        // 3. Boş HTML etiketlerini temizle (örn: <strong></strong>, <em></em>)
        html = html.replace(/<(strong|em|b|i|u|span)[^>]*>\s*<\/\1>/gi, '');
        
        // 4. Sadece açılış etiketi olan ama içerik olmayan yapıları temizle
        // Örnek: <strong> </strong> (sadece boşluk içeren)
        html = html.replace(/<(strong|em|b|i|u|span)[^>]*>\s*<\/\1>/gi, '');
        
        // 5. Self-closing etiketlerden hemen önce gelen boşlukları temizle
        html = html.replace(/\s+(<(?:br|img|hr|input)[^>]*>)/gi, '$1');
        
        // 6. Kapanış etiketlerinden önce gelen gereksiz boşlukları temizle
        html = html.replace(/\s+(<\/[^>]+>)/gi, '$1');
        
        return html;
    }
    
    escapeHtml(text) {
        // HTML karakterlerini escape et
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
            
            // Sadece ham metni döndür (formatlama sendMessage'da yapılacak)
            // Satır sonlarını normalize et (\n olarak tut)
            botResponse = botResponse.replace(/\\n/g, '\n');
            
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
        }
    }
    
    getWeatherIcon(weatherCode) {
        // Hava durumu koduna göre ikon döndür
        if (!weatherCode) return '🌤️';
        
        const code = weatherCode.toLowerCase();
        
        // Türkçe hava durumu açıklamalarına göre eşleştirme
        if (code.includes('kapalı') || code.includes('çok bulutlu') || code.includes('bulutlu')) {
            return '☁️'; // Kapalı/Bulutlu
        }
        if (code.includes('açık') || code.includes('clear') || code.includes('güneşli')) {
            return '☀️'; // Açık/Güneşli
        }
        if (code.includes('az bulutlu') || code.includes('partly') || code.includes('yarı')) {
            return '⛅'; // Yarı bulutlu
        }
        if (code.includes('yağmur') || code.includes('rain')) {
            return '🌧️'; // Yağmurlu
        }
        if (code.includes('sağanak') || code.includes('shower')) {
            return '⛈️'; // Sağanak
        }
        if (code.includes('kar') || code.includes('snow')) {
            return '❄️'; // Karlı
        }
        if (code.includes('sis') || code.includes('fog') || code.includes('mist')) {
            return '🌫️'; // Sislı
        }
        if (code.includes('fırtına') || code.includes('thunder') || code.includes('storm')) {
            return '⛈️'; // Fırtınalı
        }
        if (code.includes('rüzgar') || code.includes('wind')) {
            return '💨'; // Rüzgarlı
        }
        
        // Varsayılan
        return '🌤️';
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
            
            // Eski grafikleri temizle
            if (this.charts.weatherChart) {
                this.charts.weatherChart.destroy();
            }
            if (this.charts.apparentTemperatureChart) {
                this.charts.apparentTemperatureChart.destroy();
            }
            if (this.charts.precipitationChart) {
                this.charts.precipitationChart.destroy();
            }
            if (this.charts.windChart) {
                this.charts.windChart.destroy();
            }
            
            // Hava durumu ikonu
            const weatherIcon = this.getWeatherIcon(weatherData.weather_code);
            
            // Hava panelini verilerle güncelle
            this.weatherContent.innerHTML = `
                <div class="weather-data">
                    <div class="weather-main">
                        <div class="weather-icon-large">${weatherIcon}</div>
                        <div class="weather-temp">${weatherData.temperature ? Math.round(weatherData.temperature) : 'N/A'}°C</div>
                        <div class="weather-desc">${weatherData.weather_code || 'N/A'}</div>
                    </div>
                    <div class="weather-chart-container">
                        <canvas id="weatherChart"></canvas>
                    </div>
                    <div class="weather-details">
                        <div class="weather-apparent-temp-chart-container">
                            <div class="weather-chart-title">🌡️ Hissedilen Sıcaklık</div>
                            <canvas id="apparentTemperatureChart"></canvas>
                        </div>
                        <div class="weather-apparent-temp-chart-container">
                            <div class="weather-chart-title">🌧️ Yağış Miktarları</div>
                            <canvas id="precipitationChart"></canvas>
                        </div>
                        <div class="weather-apparent-temp-chart-container">
                            <div class="weather-chart-title">💨 Rüzgar Hızları</div>
                            <canvas id="windChart"></canvas>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">☀️</span>
                                Güneşlenme:
                            </span>
                            <span class="weather-value">${weatherData.sunshine_duration ? Math.round(weatherData.sunshine_duration/3600) : 'N/A'} saat</span>
                        </div>
                    </div>
                    <button class="panel-btn" onclick="umayChat.loadWeatherData()">Yenile</button>
                </div>
            `;
            
            // 24 saatlik grafik oluştur (örnek veri)
            setTimeout(() => {
                this.createWeatherChart(weatherData);
                this.createApparentTemperatureChart(weatherData);
                this.createPrecipitationChart(weatherData);
                this.createWindChart(weatherData);
            }, 100);
            
        } catch (error) {
            console.error('Weather API hatası:', error);
            this.weatherContent.innerHTML = `
                <div class="panel-placeholder">
                    <div class="placeholder-icon">⚠️</div>
                    <p>Hava durumu bilgileri alınamadı</p>
                    <button class="panel-btn" onclick="umayChat.loadWeatherData()">Tekrar Dene</button>
                </div>
            `;
        } finally {
            // Butonu tekrar etkinleştir
            if (this.weatherBtn) {
                this.weatherBtn.disabled = false;
                this.weatherBtn.textContent = 'Hava Durumu Al';
            }
        }
    }
    
    createWeatherChart(weatherData) {
        const ctx = document.getElementById('weatherChart');
        if (!ctx) return;
        
        // Örnek 24 saatlik veri (gerçek uygulamada API'den gelecek)
        const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
        const temperatures = Array.from({length: 24}, () => {
            const base = weatherData.temperature || 20;
            return Math.round(base + (Math.random() * 10 - 5));
        });
        const precipitation = Array.from({length: 24}, () => Math.random() * 5);
        
        if (this.charts.weatherChart) {
            this.charts.weatherChart.destroy();
        }
        
        this.charts.weatherChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours.filter((_, i) => i % 3 === 0), // Her 3 saatte bir göster
                datasets: [
                    {
                        label: 'Sıcaklık (°C)',
                        data: temperatures.filter((_, i) => i % 3 === 0),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Yağış (mm)',
                        data: precipitation.filter((_, i) => i % 3 === 0),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#EAEAEA',
                            font: { size: 10 }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#A0A0A0', font: { size: 9 } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        ticks: { color: '#A0A0A0', font: { size: 9 } },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: '#A0A0A0', font: { size: 9 } },
                        grid: { drawOnChartArea: false }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createApparentTemperatureChart(weatherData) {
        const ctx = document.getElementById('apparentTemperatureChart');
        if (!ctx) return;
        
        // Hissedilen sıcaklık değerlerini al
        const minTemp = weatherData.apparent_temperature_min ? Math.round(weatherData.apparent_temperature_min) : 0;
        const meanTemp = weatherData.apparent_temperature_mean ? Math.round(weatherData.apparent_temperature_mean) : 0;
        const maxTemp = weatherData.apparent_temperature_max ? Math.round(weatherData.apparent_temperature_max) : 0;
        
        // Eski grafiği temizle
        if (this.charts.apparentTemperatureChart) {
            this.charts.apparentTemperatureChart.destroy();
        }
        
        this.charts.apparentTemperatureChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Min', 'Ort', 'Max'],
                datasets: [{
                    label: 'Hissedilen Sıcaklık (°C)',
                    data: [minTemp, meanTemp, maxTemp],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',  // Min - Mavi
                        'rgba(16, 185, 129, 0.8)',   // Ort - Yeşil
                        'rgba(245, 158, 11, 0.8)'    // Max - Turuncu
                    ],
                    borderColor: [
                        '#3b82f6',  // Min - Mavi
                        '#10b981',  // Ort - Yeşil
                        '#f59e0b'   // Max - Turuncu
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Yatay çubuklar
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return ''; // Başlığı kaldır
                            },
                            label: function(context) {
                                // Yatay çubuk grafiklerde değer x ekseninde
                                return context.parsed.x + '°C';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 11 },
                            callback: function(value) {
                                return value + '°C';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 12, weight: '500' }
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createPrecipitationChart(weatherData) {
        const ctx = document.getElementById('precipitationChart');
        if (!ctx) return;
        
        // Yağış değerlerini al
        const rainSum = weatherData.rain_sum != null ? weatherData.rain_sum : 0;
        const showersSum = weatherData.showers_sum != null ? weatherData.showers_sum : 0;
        const snowfallSum = weatherData.snowfall_sum != null ? weatherData.snowfall_sum : 0;
        const precipitationSum = weatherData.precipitation_sum != null ? weatherData.precipitation_sum : 0;
        
        // Eski grafiği temizle
        if (this.charts.precipitationChart) {
            this.charts.precipitationChart.destroy();
        }
        
        this.charts.precipitationChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Yağmur', 'Sağanak', 'Kar', 'Toplam Yağış'],
                datasets: [{
                    label: 'Yağış Miktarı (mm)',
                    data: [rainSum, showersSum, snowfallSum, precipitationSum],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',   // Yağmur - Mavi
                        'rgba(139, 92, 246, 0.8)',   // Sağanak - Mor
                        'rgba(147, 197, 253, 0.8)',  // Kar - Açık Mavi
                        'rgba(16, 185, 129, 0.8)'    // Toplam - Yeşil
                    ],
                    borderColor: [
                        '#3b82f6',   // Yağmur - Mavi
                        '#8b5cf6',    // Sağanak - Mor
                        '#93c5fd',   // Kar - Açık Mavi
                        '#10b981'     // Toplam - Yeşil
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Yatay çubuklar
                layout: {
                    padding: {
                        left: 5,
                        right: 25,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return ''; // Başlığı kaldır
                            },
                            label: function(context) {
                                return context.parsed.x + ' mm';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        position: 'bottom',
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 9 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            maxTicksLimit: 8,
                            callback: function(value) {
                                return value + ' mm';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 11, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createWindChart(weatherData) {
        const ctx = document.getElementById('windChart');
        if (!ctx) return;
        
        // Rüzgar değerlerini al
        const windSpeedMax = weatherData.wind_speed_max || 0;
        const windGustsMax = weatherData.wind_gusts_max || 0;
        
        // Eski grafiği temizle
        if (this.charts.windChart) {
            this.charts.windChart.destroy();
        }
        
        this.charts.windChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Rüzgar Max', 'Rüzgar Böre'],
                datasets: [{
                    label: 'Rüzgar Hızı (km/h)',
                    data: [windSpeedMax, windGustsMax],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',  // Rüzgar Max - Mavi
                        'rgba(245, 158, 11, 0.8)'   // Rüzgar Böre - Turuncu
                    ],
                    borderColor: [
                        '#3b82f6',  // Rüzgar Max - Mavi
                        '#f59e0b'   // Rüzgar Böre - Turuncu
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Yatay çubuklar
                layout: {
                    padding: {
                        left: 5,
                        right: 25,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return ''; // Başlığı kaldır
                            },
                            label: function(context) {
                                return context.parsed.x + ' km/h';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        position: 'bottom',
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 9 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            maxTicksLimit: 8,
                            callback: function(value) {
                                return value + ' km/h';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 11, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
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
            
            // Eski grafikleri temizle
            Object.keys(this.charts).forEach(key => {
                if (key.startsWith('soil')) {
                    this.charts[key].destroy();
                    delete this.charts[key];
                }
            });
            
            // Toprak panelini verilerle güncelle
            let soilDetailsHTML = '';
            let hasClay = false, hasSilt = false, hasSand = false;
            
            // Grafikleri olan değerlerin listesi
            const chartedKeys = [
                'pH',
                'Organic Carbon',
                'Total Nitrogen',
                'Bulk Density',
                'Reference Bulk Density',
                'Cation Exchange Capacity',
                'Clay CEC',
                'Effective CEC',
                'Base Saturation',
                'Aluminum Saturation',
                'Exchangeable Sodium Percentage',
                'Clay',
                'Silt',
                'Sand'
            ];
            
            // Tüm özellikleri döngü ile ekle (grafikleri olanlar hariç)
            for (const [key, value] of Object.entries(soilData)) {
                if (key !== 'soil_type' && key !== 'soil_code' && key !== 'description' && value !== 'N/A' && value !== null) {
                    // Kil, silt, kum kontrolü (sadece Toprak Bileşimi grafiği için)
                    if (key === 'Clay') hasClay = true;
                    if (key === 'Silt') hasSilt = true;
                    if (key === 'Sand') hasSand = true;
                    
                    // Grafikleri olan değerleri atla
                    if (chartedKeys.includes(key)) {
                        continue;
                    }
                    
                    // Label'ı Türkçe'ye çevir
                    let label = key;
                    const labelMap = {
                        'C/N Ratio': 'C/N Oranı',
                        'Coarse Fragments': 'Kaba Parçacıklar',
                        'Root Depth': 'Kök Derinliği',
                        'Available Water Capacity': 'Su Kapasitesi',
                        'Total Exchangeable Bases': 'Toplam Değişebilir Bazlar',
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
            
            // Grafikler için HTML
            let chartsHTML = '';
            
            // pH Gauge
            if (soilData.pH != null && soilData.pH !== 'N/A') {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">pH Değeri</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilPHGauge"></canvas>
                        </div>
                    </div>
                `;
            }
            
            // Organik Madde ve Toplam Azot
            if ((soilData['Organic Carbon'] != null && soilData['Organic Carbon'] !== 'N/A') || 
                (soilData['Total Nitrogen'] != null && soilData['Total Nitrogen'] !== 'N/A')) {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">Organik Madde ve Toplam Azot</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilOrganicChart"></canvas>
                        </div>
                    </div>
                `;
            }
            
            // Yoğunluk karşılaştırması
            if ((soilData['Bulk Density'] != null && soilData['Bulk Density'] !== 'N/A') || 
                (soilData['Reference Bulk Density'] != null && soilData['Reference Bulk Density'] !== 'N/A')) {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">Yoğunluk Karşılaştırması</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilDensityChart"></canvas>
                        </div>
                    </div>
                `;
            }
            
            // Katyon Değişim Kapasitesi
            if ((soilData['Cation Exchange Capacity'] != null && soilData['Cation Exchange Capacity'] !== 'N/A') ||
                (soilData['Clay CEC'] != null && soilData['Clay CEC'] !== 'N/A') ||
                (soilData['Effective CEC'] != null && soilData['Effective CEC'] !== 'N/A')) {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">Katyon Değişim Kapasitesi</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilCECChart"></canvas>
                        </div>
                    </div>
                `;
            }
            
            // Doygunluk değerleri
            if ((soilData['Base Saturation'] != null && soilData['Base Saturation'] !== 'N/A') ||
                (soilData['Aluminum Saturation'] != null && soilData['Aluminum Saturation'] !== 'N/A') ||
                (soilData['Exchangeable Sodium Percentage'] != null && soilData['Exchangeable Sodium Percentage'] !== 'N/A')) {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">Doygunluk Değerleri</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilSaturationChart"></canvas>
                        </div>
                    </div>
                `;
            }
            
            // Kil/Silt/Kum Pie Chart (Toprak Bileşimi)
            if (hasClay && hasSilt && hasSand) {
                chartsHTML += `
                    <div class="soil-chart-item">
                        <div class="soil-chart-title">Toprak Bileşimi</div>
                        <div class="soil-chart-canvas">
                            <canvas id="soilCompositionChart"></canvas>
                        </div>
                    </div>
                `;
            }
            
            this.soilContent.innerHTML = `
                <div class="soil-data">
                    <div class="soil-main">
                        <div class="soil-type">${soilData.soil_type || 'Bilinmiyor'}</div>
                        <div class="soil-desc">${soilData.description || 'Toprak analizi yapılamadı'}</div>
                    </div>
                    ${chartsHTML ? `<div class="soil-charts-container">${chartsHTML}</div>` : ''}
                    <div class="soil-details">
                        ${soilDetailsHTML}
                    </div>
                    <button class="panel-btn" onclick="umayChat.loadSoilData()">Yenile</button>
                </div>
            `;
            
            // Grafikleri oluştur
            setTimeout(() => {
                // pH Gauge
                if (soilData.pH != null && soilData.pH !== 'N/A') {
                    const pHValue = parseFloat(soilData.pH.toString().replace(' pH units', '').replace(' pH', '')) || 0;
                    this.createPHGauge(pHValue);
                }
                
                // Organik Madde ve Toplam Azot
                if ((soilData['Organic Carbon'] != null && soilData['Organic Carbon'] !== 'N/A') || 
                    (soilData['Total Nitrogen'] != null && soilData['Total Nitrogen'] !== 'N/A')) {
                    const organicCarbon = parseFloat(soilData['Organic Carbon']?.toString().replace('%', '') || '0');
                    const totalNitrogen = parseFloat(soilData['Total Nitrogen']?.toString().replace('%', '') || '0');
                    this.createSoilOrganicChart(organicCarbon, totalNitrogen);
                }
                
                // Yoğunluk karşılaştırması
                if ((soilData['Bulk Density'] != null && soilData['Bulk Density'] !== 'N/A') || 
                    (soilData['Reference Bulk Density'] != null && soilData['Reference Bulk Density'] !== 'N/A')) {
                    const bulkDensity = parseFloat(soilData['Bulk Density']?.toString().replace(' g/cm³', '') || '0');
                    const refBulkDensity = parseFloat(soilData['Reference Bulk Density']?.toString().replace(' g/cm³', '') || '0');
                    this.createSoilDensityChart(bulkDensity, refBulkDensity);
                }
                
                // Katyon Değişim Kapasitesi
                if ((soilData['Cation Exchange Capacity'] != null && soilData['Cation Exchange Capacity'] !== 'N/A') ||
                    (soilData['Clay CEC'] != null && soilData['Clay CEC'] !== 'N/A') ||
                    (soilData['Effective CEC'] != null && soilData['Effective CEC'] !== 'N/A')) {
                    const cec = parseFloat(soilData['Cation Exchange Capacity']?.toString().replace(' cmol/kg', '') || '0');
                    const clayCEC = parseFloat(soilData['Clay CEC']?.toString().replace(' cmol/kg', '') || '0');
                    const effectiveCEC = parseFloat(soilData['Effective CEC']?.toString().replace(' cmol/kg', '') || '0');
                    this.createSoilCECChart(cec, clayCEC, effectiveCEC);
                }
                
                // Doygunluk değerleri
                if ((soilData['Base Saturation'] != null && soilData['Base Saturation'] !== 'N/A') ||
                    (soilData['Aluminum Saturation'] != null && soilData['Aluminum Saturation'] !== 'N/A') ||
                    (soilData['Exchangeable Sodium Percentage'] != null && soilData['Exchangeable Sodium Percentage'] !== 'N/A')) {
                    const baseSat = parseFloat(soilData['Base Saturation']?.toString().replace('%', '') || '0');
                    const aluminumSat = parseFloat(soilData['Aluminum Saturation']?.toString().replace('%', '') || '0');
                    const sodiumPct = parseFloat(soilData['Exchangeable Sodium Percentage']?.toString().replace('%', '') || '0');
                    this.createSoilSaturationChart(baseSat, aluminumSat, sodiumPct);
                }
                
                // Toprak Bileşimi
                if (hasClay && hasSilt && hasSand) {
                    this.createSoilCompositionChart(
                        parseFloat(soilData['Clay']) || 0,
                        parseFloat(soilData['Silt']) || 0,
                        parseFloat(soilData['Sand']) || 0
                    );
                }
            }, 200);
            
        } catch (error) {
            console.error('Soil API hatası:', error);
            this.soilContent.innerHTML = `
                <div class="panel-placeholder">
                    <div class="placeholder-icon">⚠️</div>
                    <p>Toprak analizi bilgileri alınamadı</p>
                    <button class="panel-btn" onclick="umayChat.loadSoilData()">Tekrar Dene</button>
                </div>
            `;
        } finally {
            // Butonu tekrar etkinleştir
            if (this.soilBtn) {
                this.soilBtn.disabled = false;
                this.soilBtn.textContent = 'Toprak Analizi Al';
            }
        }
    }
    
    createPHGauge(pHValue) {
        const canvas = document.getElementById('soilPHGauge');
        if (!canvas) return;
        
        // Canvas boyutunu ayarla
        const container = canvas.parentElement;
        if (container) {
            canvas.width = container.offsetWidth;
            canvas.height = container.offsetHeight || 120;
        }
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // pH değerini 0-14 arasına sınırla
        const clampedPH = Math.max(0, Math.min(14, pHValue));
        
        // pH durumunu belirle
        let pHStatus = '';
        let statusColor = '#EAEAEA';
        if (clampedPH < 4.5) {
            pHStatus = 'Çok Asidik';
            statusColor = '#ef4444';
        } else if (clampedPH < 5.5) {
            pHStatus = 'Asidik';
            statusColor = '#f97316';
        } else if (clampedPH < 6.5) {
            pHStatus = 'Hafif Asidik';
            statusColor = '#fbbf24';
        } else if (clampedPH < 7.5) {
            pHStatus = 'Nötr';
            statusColor = '#10b981';
        } else if (clampedPH < 8.5) {
            pHStatus = 'Hafif Bazik';
            statusColor = '#3b82f6';
        } else if (clampedPH < 9.5) {
            pHStatus = 'Bazik';
            statusColor = '#6366f1';
        } else {
            pHStatus = 'Çok Bazik';
            statusColor = '#8b5cf6';
        }
        
        // pH cetveli parametreleri
        const scaleHeight = 30;
        const scaleY = height / 2 - scaleHeight / 2;
        const scaleWidth = width - 40;
        const scaleX = 20;
        const stepWidth = scaleWidth / 14;
        
        // pH cetveli gradyanı çiz (14 segment: 0-1, 1-2, ..., 13-14)
        for (let i = 0; i < 14; i++) {
            const x = scaleX + (i * stepWidth);
            let r, g, b;
            
            // pH değerine göre renk (0: kırmızı, 7: yeşil, 14: mor)
            // Her segment için orta noktasını kullan
            const segmentValue = i + 0.5;
            
            if (segmentValue < 7) {
                // Asidik: kırmızıdan sarıya
                r = 255;
                g = Math.round(255 * (segmentValue / 7));
                b = 0;
            } else if (segmentValue === 7) {
                // Nötr: yeşil
                r = 16;
                g = 185;
                b = 129;
            } else {
                // Bazik: maviden mora
                r = Math.round(255 * ((14 - segmentValue) / 7));
                g = Math.round(255 * ((14 - segmentValue) / 7));
                b = 255;
            }
            
            ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            ctx.fillRect(x, scaleY, stepWidth, scaleHeight);
        }
        
        // pH cetveli çerçevesi
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 2;
        ctx.strokeRect(scaleX, scaleY, scaleWidth, scaleHeight);
        
        // pH değerinin konumunu göster
        const pHX = scaleX + (clampedPH * stepWidth);
        ctx.strokeStyle = '#EAEAEA';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(pHX, scaleY - 5);
        ctx.lineTo(pHX, scaleY + scaleHeight + 5);
        ctx.stroke();
        
        // pH değerini göster (üstte)
        ctx.fillStyle = '#EAEAEA';
        ctx.font = 'bold 20px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(clampedPH.toFixed(1), pHX, scaleY - 20);
        
        // pH durumunu göster (altta)
        ctx.fillStyle = statusColor;
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.fillText(pHStatus, pHX, scaleY + scaleHeight + 25);
        
        // pH cetveli işaretleri (0, 7, 14)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        // 0 işareti
        ctx.fillText('0', scaleX, scaleY + scaleHeight + 5);
        
        // 7 işareti (nötr)
        const neutralX = scaleX + (7 * stepWidth);
        ctx.fillText('7', neutralX, scaleY + scaleHeight + 5);
        
        // 14 işareti
        ctx.fillText('14', scaleX + scaleWidth, scaleY + scaleHeight + 5);
    }
    
    createSoilCompositionChart(clay, silt, sand) {
        const ctx = document.getElementById('soilCompositionChart');
        if (!ctx) return;
        
        const total = clay + silt + sand;
        if (total === 0) return;
        
        if (this.charts.soilCompositionChart) {
            this.charts.soilCompositionChart.destroy();
        }
        
        this.charts.soilCompositionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Kil', 'Silt', 'Kum'],
                datasets: [{
                    data: [clay, silt, sand],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#3b82f6',
                        '#f59e0b'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#EAEAEA',
                            font: { size: 11 },
                            padding: 15
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createSoilDensityChart(bulkDensity, refBulkDensity) {
        const ctx = document.getElementById('soilDensityChart');
        if (!ctx) return;
        
        if (this.charts.soilDensityChart) {
            this.charts.soilDensityChart.destroy();
        }
        
        this.charts.soilDensityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mevcut Yoğunluk', 'Referans Yoğunluk'],
                datasets: [{
                    label: 'Yoğunluk (g/cm³)',
                    data: [bulkDensity, refBulkDensity],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#3b82f6'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        left: 5,
                        right: 15,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return '';
                            },
                            label: function(context) {
                                return context.parsed.x + ' g/cm³';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 10 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            callback: function(value) {
                                return value + ' g/cm³';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 11, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createSoilOrganicChart(organicCarbon, totalNitrogen) {
        const ctx = document.getElementById('soilOrganicChart');
        if (!ctx) return;
        
        if (this.charts.soilOrganicChart) {
            this.charts.soilOrganicChart.destroy();
        }
        
        this.charts.soilOrganicChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Organik Madde', 'Toplam Azot'],
                datasets: [{
                    label: 'Değer (%)',
                    data: [organicCarbon, totalNitrogen],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#3b82f6'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        left: 5,
                        right: 15,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return '';
                            },
                            label: function(context) {
                                return context.parsed.x + ' %';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 10 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            callback: function(value) {
                                return value + ' %';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 11, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createSoilCECChart(cec, clayCEC, effectiveCEC) {
        const ctx = document.getElementById('soilCECChart');
        if (!ctx) return;
        
        if (this.charts.soilCECChart) {
            this.charts.soilCECChart.destroy();
        }
        
        this.charts.soilCECChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['CEC', 'Kil CEC', 'Etkili CEC'],
                datasets: [{
                    label: 'Katyon Değişim Kapasitesi (cmol/kg)',
                    data: [cec, clayCEC, effectiveCEC],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#3b82f6',
                        '#f59e0b'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        left: 5,
                        right: 20,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return '';
                            },
                            label: function(context) {
                                return context.parsed.x + ' cmol/kg';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 9 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            callback: function(value) {
                                return value + ' cmol/kg';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 11, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    createSoilSaturationChart(baseSat, aluminumSat, sodiumPct) {
        const ctx = document.getElementById('soilSaturationChart');
        if (!ctx) return;
        
        if (this.charts.soilSaturationChart) {
            this.charts.soilSaturationChart.destroy();
        }
        
        this.charts.soilSaturationChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Baz Doygunluğu', 'Alüminyum Doygunluğu', 'Değişebilir Sodyum Yüzdesi'],
                datasets: [{
                    label: 'Doygunluk (%)',
                    data: [baseSat, aluminumSat, sodiumPct],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(59, 130, 246, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#f59e0b',
                        '#3b82f6'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        left: 5,
                        right: 15,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return '';
                            },
                            label: function(context) {
                                return context.parsed.x + ' %';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 9 },
                            maxRotation: 0,
                            minRotation: 0,
                            padding: 3,
                            callback: function(value) {
                                return value + ' %';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#EAEAEA',
                            font: { size: 10, weight: '500' },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
}

// Global instance
let umayChat;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    umayChat = new UmayChat();
});

// Typing indicator stilleri CSS'te zaten var, ek bir stil gerekmiyor

