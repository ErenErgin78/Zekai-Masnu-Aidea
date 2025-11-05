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
        
        // Bot cevabını API'den al ve streaming olarak göster
        try {
            const botResponse = await this.getBotResponse(message);
            this.hideTyping();
            
            // Önce formatlamayı yap (markdown ve HTML etiketleri)
            const formattedResponse = this.formatMessage(botResponse);
            
            // Formatlanmış metni streaming olarak kelime kelime göster
            this.streamMessage(formattedResponse, 'bot');
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
        // Basit biçimleme
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    escapeHtml(text) {
        // HTML karakterlerini escape et
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    streamMessage(content, sender) {
        // Mesajı streaming olarak kelime kelime göster
        const message = {
            content: '',
            sender,
            timestamp: new Date().toLocaleTimeString('tr-TR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }),
            streaming: true
        };
        
        // Mesaj div'ini oluştur
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        const bubbleId = 'streamingBubble_' + Date.now();
        messageDiv.innerHTML = `
            <div class="message-bubble" id="${bubbleId}"></div>
            <div class="message-time">${message.timestamp}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        const bubbleElement = document.getElementById(bubbleId);
        
        // Scroll kontrolü için - kullanıcı scroll yaptıysa otomatik scroll yapma
        let shouldAutoScroll = true;
        let userScrolled = false;
        let scrollTimeout = null;
        
        // Kullanıcının en altta olup olmadığını kontrol et
        const isNearBottom = () => {
            const threshold = 100; // 100px tolerans
            const scrollTop = this.chatMessages.scrollTop;
            const scrollHeight = this.chatMessages.scrollHeight;
            const clientHeight = this.chatMessages.clientHeight;
            return (scrollHeight - scrollTop - clientHeight) < threshold;
        };
        
        // Scroll event listener - kullanıcı scroll yaptıysa otomatik scroll'u durdur
        const handleScroll = () => {
            // Kullanıcı scroll yaptıysa işaretle
            if (!userScrolled) {
                userScrolled = true;
                shouldAutoScroll = false;
            }
            
            // Scroll timeout'u temizle
            if (scrollTimeout) {
                clearTimeout(scrollTimeout);
            }
            
            // Kullanıcı scroll'u durdurduktan 500ms sonra kontrol et
            scrollTimeout = setTimeout(() => {
                // Kullanıcı en alta tekrar scroll yaptıysa otomatik scroll'u etkinleştir
                if (isNearBottom()) {
                    userScrolled = false;
                    shouldAutoScroll = true;
                }
            }, 500);
        };
        
        // Scroll event listener'ı ekle
        this.chatMessages.addEventListener('scroll', handleScroll, { passive: true });
        
        // HTML etiketlerini ve içeriklerini koruyarak tokenize et
        // Önce HTML etiketlerini (açılış+kapanış ve içerik) ve metni ayrı ayrı bul
        const tokens = [];
        let processedContent = content;
        let lastIndex = 0;
        
        // HTML etiketlerini ve içeriklerini bul (örn: <strong>text</strong>)
        const htmlTagRegex = /<(\w+)[^>]*>([^<]*)<\/\1>/g;
        let match;
        
        while ((match = htmlTagRegex.exec(processedContent)) !== null) {
            // Etiket öncesi metni ekle
            if (match.index > lastIndex) {
                const beforeText = processedContent.substring(lastIndex, match.index);
                if (beforeText.trim()) {
                    tokens.push(...beforeText.split(/(\s+)/).filter(t => t !== ''));
                }
            }
            
            // HTML etiketini ve içeriğini tek token olarak ekle
            tokens.push(match[0]); // <strong>text</strong>
            
            lastIndex = match.index + match[0].length;
        }
        
        // Kalan metni ekle
        if (lastIndex < processedContent.length) {
            const remainingText = processedContent.substring(lastIndex);
            if (remainingText.trim()) {
                tokens.push(...remainingText.split(/(\s+)/).filter(t => t !== ''));
            }
        }
        
        // Tek başına kalan HTML etiketlerini de bul (<br>, <strong></strong> gibi)
        // Önce HTML etiketlerini placeholder'lara çevir
        const tagPlaceholders = {};
        let placeholderIndex = 0;
        const standaloneTagRegex = /<[^>]+>/g;
        
        for (let i = 0; i < tokens.length; i++) {
            // Tek başına HTML etiketi varsa (<br>, <strong></strong> gibi)
            if (standaloneTagRegex.test(tokens[i]) && !tokens[i].includes('</')) {
                // Eğer bu token zaten bir HTML etiketi içeriyorsa (önceki regex ile yakalanmamışsa)
                const tagMatch = tokens[i].match(/<[^>]+>/);
                if (tagMatch && !tokens[i].includes('</')) {
                    const placeholder = `__HTMLTAG_${placeholderIndex}__`;
                    tagPlaceholders[placeholder] = tokens[i];
                    tokens[i] = placeholder;
                    placeholderIndex++;
                }
            }
        }
        
        let currentIndex = 0;
        
        // Streaming fonksiyonu - smooth fade-in efekti ile
        const streamWord = () => {
            if (currentIndex < tokens.length) {
                // Token'ı al
                let token = tokens[currentIndex];
                let isPlaceholder = false;
                let isHtmlTag = false;
                
                // Placeholder kontrolü - tam eşleşme varsa token'ı değiştir
                for (const [placeholder, tag] of Object.entries(tagPlaceholders)) {
                    if (token === placeholder) {
                        token = tag;
                        isPlaceholder = true;
                        isHtmlTag = true;
                        break;
                    } else if (token.includes(placeholder)) {
                        token = token.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), tag);
                        isHtmlTag = true;
                    }
                }
                
                // HTML etiketi kontrolü (tam etiket: <strong>text</strong> veya tek etiket: <br>)
                if (!isHtmlTag && token.trim().startsWith('<')) {
                    isHtmlTag = true;
                }
                
                // HTML etiketi kontrolü
                if (isPlaceholder || isHtmlTag) {
                    // HTML etiketi - parse et ve ekle
                    if (token.trim() === '<br>' || token.trim() === '<br/>' || token.trim() === '<br />') {
                        // <br> etiketi - line break ekle
                        bubbleElement.appendChild(document.createElement('br'));
                        message.content += '<br>';
                    } else if (token.trim().match(/<(\w+)[^>]*>.*?<\/\1>/)) {
                        // Tam HTML etiketi (örn: <strong>text</strong>) - parse et ve içindeki metni animasyonlu ekle
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = token;
                        
                        // HTML elemanını al (örn: <strong>)
                        const htmlElement = tempDiv.firstElementChild;
                        if (htmlElement) {
                            // İçindeki metni al
                            const innerText = htmlElement.textContent;
                            // HTML elemanını klonla
                            const clonedElement = htmlElement.cloneNode(false); // Sadece elemanı klonla, içeriği değil
                            
                            // İçindeki metni kelime kelime ayır ve animasyonlu ekle
                            if (innerText.trim()) {
                                const words = innerText.split(/(\s+)/).filter(w => w !== '');
                                words.forEach(word => {
                                    if (word.trim().length === 0) {
                                        // Boşluk
                                        clonedElement.appendChild(document.createTextNode(word));
                                    } else {
                                        // Kelime - span ile sar ve animasyon ekle
                                        const wordSpan = document.createElement('span');
                                        wordSpan.className = 'streaming-word';
                                        wordSpan.textContent = word;
                                        clonedElement.appendChild(wordSpan);
                                        
                                        // Animasyonu tetikle
                                        requestAnimationFrame(() => {
                                            wordSpan.style.opacity = '0';
                                            wordSpan.style.transform = 'translateX(-5px)';
                                            requestAnimationFrame(() => {
                                                wordSpan.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                                                wordSpan.style.opacity = '1';
                                                wordSpan.style.transform = 'translateX(0)';
                                            });
                                        });
                                    }
                                });
                            }
                            
                            // Elemanı bubble'a ekle
                            bubbleElement.appendChild(clonedElement);
                        } else {
                            // Parse edilemediyse direkt innerHTML ile ekle
                            const tempDiv2 = document.createElement('div');
                            tempDiv2.innerHTML = token;
                            while (tempDiv2.firstChild) {
                                bubbleElement.appendChild(tempDiv2.firstChild);
                            }
                        }
                        message.content += token;
                    } else {
                        // Diğer HTML etiketleri - innerHTML ile parse et
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = token;
                        while (tempDiv.firstChild) {
                            bubbleElement.appendChild(tempDiv.firstChild);
                        }
                        message.content += token;
                    }
                } else if (token.trim().length === 0) {
                    // Boşluk - text node olarak ekle
                    bubbleElement.appendChild(document.createTextNode(token));
                    message.content += token;
                } else {
                    // Kelime - span ile sar ve animasyon ekle
                    const wordSpan = document.createElement('span');
                    wordSpan.className = 'streaming-word';
                    wordSpan.textContent = token;
                    
                    // Bubble'a direkt ekle
                    bubbleElement.appendChild(wordSpan);
                    
                    // Animasyonu tetiklemek için requestAnimationFrame kullan
                    requestAnimationFrame(() => {
                        wordSpan.style.opacity = '0';
                        wordSpan.style.transform = 'translateX(-5px)';
                        // Animasyonu başlat
                        requestAnimationFrame(() => {
                            wordSpan.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                            wordSpan.style.opacity = '1';
                            wordSpan.style.transform = 'translateX(0)';
                        });
                    });
                    
                    // message.content'i güncelle (kayıt için)
                    message.content += `<span class="streaming-word">${this.escapeHtml(token)}</span>`;
                }
                
                // Scroll kontrolü ile scroll yap - sadece kullanıcı en alttayken
                if (shouldAutoScroll && isNearBottom()) {
                    this.scrollToBottom();
                }
                
                currentIndex++;
                
                // Kelime hızı (msn cinsinden) - İKİ KAT HIZLI (yarıya indirilmiş)
                // Kelimeler için 25ms (eski 50ms), boşluklar için 10ms (eski 20ms), HTML etiketleri için 5ms (eski 10ms)
                let delay = 25;
                if (token.trim().length === 0) {
                    delay = 10; // Boşluk
                } else if (token.trim().startsWith('<') || token.trim().startsWith('&')) {
                    delay = 5; // HTML etiketi veya HTML entity
                }
                
                setTimeout(streamWord, delay);
            } else {
                // Streaming tamamlandı
                // Event listener'ı kaldır
                this.chatMessages.removeEventListener('scroll', handleScroll);
                
                // Scroll timeout'u temizle
                if (scrollTimeout) {
                    clearTimeout(scrollTimeout);
                }
                
                // Streaming tamamlandı - formatlama zaten streaming başlamadan önce yapıldı
                // Sadece final içeriği kaydet
                message.content = bubbleElement.innerHTML;
                
                // Son bir kez scroll yap - sadece kullanıcı en alttayken
                if (!userScrolled || isNearBottom()) {
                    this.scrollToBottom();
                }
                
                setTimeout(() => {
                    message.streaming = false;
                    this.messages.push(message);
                    this.saveMessages();
                }, 100);
            }
        };
        
        // Streaming'i başlat
        streamWord();
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
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">🌡️</span>
                                Hissedilen Min:
                            </span>
                            <span class="weather-value">${weatherData.apparent_temperature_min ? Math.round(weatherData.apparent_temperature_min) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">🌡️</span>
                                Hissedilen Ort:
                            </span>
                            <span class="weather-value">${weatherData.apparent_temperature_mean ? Math.round(weatherData.apparent_temperature_mean) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">🌡️</span>
                                Hissedilen Max:
                            </span>
                            <span class="weather-value">${weatherData.apparent_temperature_max ? Math.round(weatherData.apparent_temperature_max) : 'N/A'}°C</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">🌧️</span>
                                Yağmur:
                            </span>
                            <span class="weather-value">${weatherData.rain_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">⛈️</span>
                                Sağanak:
                            </span>
                            <span class="weather-value">${weatherData.showers_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">❄️</span>
                                Kar:
                            </span>
                            <span class="weather-value">${weatherData.snowfall_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">💧</span>
                                Toplam Yağış:
                            </span>
                            <span class="weather-value">${weatherData.precipitation_sum || 'N/A'} mm</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">💨</span>
                                Rüzgar Max:
                            </span>
                            <span class="weather-value">${weatherData.wind_speed_max || 'N/A'} km/h</span>
                        </div>
                        <div class="weather-item">
                            <span class="weather-label">
                                <span class="weather-label-icon">🌪️</span>
                                Rüzgar Böre:
                            </span>
                            <span class="weather-value">${weatherData.wind_gusts_max || 'N/A'} km/h</span>
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
            
            // Tüm özellikleri döngü ile ekle
            for (const [key, value] of Object.entries(soilData)) {
                if (key !== 'soil_type' && key !== 'soil_code' && key !== 'description' && value !== 'N/A' && value !== null) {
                    // Kil, silt, kum kontrolü (sadece Toprak Bileşimi grafiği için)
                    if (key === 'Clay') hasClay = true;
                    if (key === 'Silt') hasSilt = true;
                    if (key === 'Sand') hasSand = true;
                    
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
            
            // Grafikler için HTML - Sadece Toprak Bileşimi
            let chartsHTML = '';
            
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
            
            // Grafikleri oluştur - Sadece Toprak Bileşimi
            setTimeout(() => {
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
        
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 60;
        
        // pH değerine göre renk (0-14 arası)
        const normalizedValue = Math.max(0, Math.min(14, pHValue)) / 14;
        const angle = Math.PI * normalizedValue; // 0-180 derece
        
        // Renk gradyanı (asit: kırmızı, nötr: yeşil, baz: mavi)
        let color;
        if (pHValue < 7) {
            color = `rgba(${255}, ${Math.round(255 * (pHValue / 7))}, 0, 0.8)`;
        } else if (pHValue === 7) {
            color = '#10b981';
        } else {
            color = `rgba(0, ${Math.round(255 * ((14 - pHValue) / 7))}, 255, 0.8)`;
        }
        
        // Arka plan yay
        ctx.beginPath();
        ctx.arc(centerX, centerY + 20, radius, Math.PI, 0, false);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 15;
        ctx.stroke();
        
        // Değer yayı
        ctx.beginPath();
        ctx.arc(centerX, centerY + 20, radius, Math.PI, Math.PI - angle, false);
        ctx.strokeStyle = color;
        ctx.lineWidth = 15;
        ctx.lineCap = 'round';
        ctx.stroke();
        
        // İşaretler
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 2;
        for (let i = 0; i <= 14; i++) {
            const markAngle = Math.PI - (Math.PI * i / 14);
            const x1 = centerX + Math.cos(markAngle) * (radius - 10);
            const y1 = centerY + 20 + Math.sin(markAngle) * (radius - 10);
            const x2 = centerX + Math.cos(markAngle) * (radius + 5);
            const y2 = centerY + 20 + Math.sin(markAngle) * (radius + 5);
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
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
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 10 }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#A0A0A0',
                            font: { size: 10 }
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

