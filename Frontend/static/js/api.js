// API çağrıları - Chat, Weather ve Soil API'leri

/**
 * Chatbot API'sinden bot cevabı alır
 * @param {string} userMessage - Kullanıcı mesajı
 * @returns {Promise<string>} Bot cevabı
 */
async function getBotResponse(userMessage) {
    try {
        // API'ye istek gönder
        const response = await fetch('http://localhost:8001/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: userMessage,
                user_location: await getCurrentLocation()
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

/**
 * Hava durumu verilerini API'den alır ve paneli günceller
 * @param {Object} umayChatInstance - UmayChat instance'ı
 */
async function loadWeatherData(umayChatInstance) {
    if (!umayChatInstance.weatherBtn || !umayChatInstance.weatherContent) return;
    
    // Butonu devre dışı bırak
    umayChatInstance.weatherBtn.disabled = true;
    umayChatInstance.weatherBtn.textContent = 'Yükleniyor...';
    
    try {
        // Konum bilgisini al
        const location = await getCurrentLocation();
        
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
        if (umayChatInstance.charts.weatherChart) {
            umayChatInstance.charts.weatherChart.destroy();
        }
        if (umayChatInstance.charts.apparentTemperatureChart) {
            umayChatInstance.charts.apparentTemperatureChart.destroy();
        }
        if (umayChatInstance.charts.precipitationChart) {
            umayChatInstance.charts.precipitationChart.destroy();
        }
        if (umayChatInstance.charts.windChart) {
            umayChatInstance.charts.windChart.destroy();
        }
        
        // Hava durumu ikonu
        const weatherIcon = getWeatherIcon(weatherData.weather_code);
        
        // Hava panelini verilerle güncelle
        umayChatInstance.weatherContent.innerHTML = `
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
            createWeatherChart(umayChatInstance, weatherData);
            createApparentTemperatureChart(umayChatInstance, weatherData);
            createPrecipitationChart(umayChatInstance, weatherData);
            createWindChart(umayChatInstance, weatherData);
        }, 100);
        
    } catch (error) {
        console.error('Weather API hatası:', error);
        umayChatInstance.weatherContent.innerHTML = `
            <div class="panel-placeholder">
                <div class="placeholder-icon">⚠️</div>
                <p>Hava durumu bilgileri alınamadı</p>
                <button class="panel-btn" onclick="umayChat.loadWeatherData()">Tekrar Dene</button>
            </div>
        `;
    } finally {
        // Butonu tekrar etkinleştir
        if (umayChatInstance.weatherBtn) {
            umayChatInstance.weatherBtn.disabled = false;
            umayChatInstance.weatherBtn.textContent = 'Hava Durumu Al';
        }
    }
}

/**
 * Toprak analizi verilerini API'den alır ve paneli günceller
 * @param {Object} umayChatInstance - UmayChat instance'ı
 */
async function loadSoilData(umayChatInstance) {
    if (!umayChatInstance.soilBtn || !umayChatInstance.soilContent) return;
    
    // Butonu devre dışı bırak
    umayChatInstance.soilBtn.disabled = true;
    umayChatInstance.soilBtn.textContent = 'Yükleniyor...';
    
    try {
        // Konum bilgisini al
        const location = await getCurrentLocation();
        
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
        Object.keys(umayChatInstance.charts).forEach(key => {
            if (key.startsWith('soil')) {
                umayChatInstance.charts[key].destroy();
                delete umayChatInstance.charts[key];
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
        
        umayChatInstance.soilContent.innerHTML = `
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
                createPHGauge(umayChatInstance, pHValue);
            }
            
            // Organik Madde ve Toplam Azot
            if ((soilData['Organic Carbon'] != null && soilData['Organic Carbon'] !== 'N/A') || 
                (soilData['Total Nitrogen'] != null && soilData['Total Nitrogen'] !== 'N/A')) {
                const organicCarbon = parseFloat(soilData['Organic Carbon']?.toString().replace('%', '') || '0');
                const totalNitrogen = parseFloat(soilData['Total Nitrogen']?.toString().replace('%', '') || '0');
                createSoilOrganicChart(umayChatInstance, organicCarbon, totalNitrogen);
            }
            
            // Yoğunluk karşılaştırması
            if ((soilData['Bulk Density'] != null && soilData['Bulk Density'] !== 'N/A') || 
                (soilData['Reference Bulk Density'] != null && soilData['Reference Bulk Density'] !== 'N/A')) {
                const bulkDensity = parseFloat(soilData['Bulk Density']?.toString().replace(' g/cm³', '') || '0');
                const refBulkDensity = parseFloat(soilData['Reference Bulk Density']?.toString().replace(' g/cm³', '') || '0');
                createSoilDensityChart(umayChatInstance, bulkDensity, refBulkDensity);
            }
            
            // Katyon Değişim Kapasitesi
            if ((soilData['Cation Exchange Capacity'] != null && soilData['Cation Exchange Capacity'] !== 'N/A') ||
                (soilData['Clay CEC'] != null && soilData['Clay CEC'] !== 'N/A') ||
                (soilData['Effective CEC'] != null && soilData['Effective CEC'] !== 'N/A')) {
                const cec = parseFloat(soilData['Cation Exchange Capacity']?.toString().replace(' cmol/kg', '') || '0');
                const clayCEC = parseFloat(soilData['Clay CEC']?.toString().replace(' cmol/kg', '') || '0');
                const effectiveCEC = parseFloat(soilData['Effective CEC']?.toString().replace(' cmol/kg', '') || '0');
                createSoilCECChart(umayChatInstance, cec, clayCEC, effectiveCEC);
            }
            
            // Doygunluk değerleri
            if ((soilData['Base Saturation'] != null && soilData['Base Saturation'] !== 'N/A') ||
                (soilData['Aluminum Saturation'] != null && soilData['Aluminum Saturation'] !== 'N/A') ||
                (soilData['Exchangeable Sodium Percentage'] != null && soilData['Exchangeable Sodium Percentage'] !== 'N/A')) {
                const baseSat = parseFloat(soilData['Base Saturation']?.toString().replace('%', '') || '0');
                const aluminumSat = parseFloat(soilData['Aluminum Saturation']?.toString().replace('%', '') || '0');
                const sodiumPct = parseFloat(soilData['Exchangeable Sodium Percentage']?.toString().replace('%', '') || '0');
                createSoilSaturationChart(umayChatInstance, baseSat, aluminumSat, sodiumPct);
            }
            
            // Toprak Bileşimi
            if (hasClay && hasSilt && hasSand) {
                createSoilCompositionChart(
                    umayChatInstance,
                    parseFloat(soilData['Clay']) || 0,
                    parseFloat(soilData['Silt']) || 0,
                    parseFloat(soilData['Sand']) || 0
                );
            }
        }, 200);
        
    } catch (error) {
        console.error('Soil API hatası:', error);
        umayChatInstance.soilContent.innerHTML = `
            <div class="panel-placeholder">
                <div class="placeholder-icon">⚠️</div>
                <p>Toprak analizi bilgileri alınamadı</p>
                <button class="panel-btn" onclick="umayChat.loadSoilData()">Tekrar Dene</button>
            </div>
        `;
    } finally {
        // Butonu tekrar etkinleştir
        if (umayChatInstance.soilBtn) {
            umayChatInstance.soilBtn.disabled = false;
            umayChatInstance.soilBtn.textContent = 'Toprak Analizi Al';
        }
    }
}

/**
 * Kullanıcı girişi yapar ve token alır
 * @param {string} username - Kullanıcı adı
 * @param {string} password - Şifre
 * @returns {Promise<Object>} Token bilgisi {access_token, token_type}
 */
async function loginUser(username, password) {
    try {
        // FormData oluştur (OAuth2PasswordRequestForm formatı)
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        // API'ye istek gönder (Backend API port 8000'de çalışıyor)
        const response = await fetch('http://localhost:8000/users/token', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Giriş başarısız' }));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Login API response:', data);
        
        // Token'ı localStorage'a kaydet
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('token_type', data.token_type || 'bearer');
            console.log('Token localStorage\'a kaydedildi');
        } else {
            console.warn('Token bulunamadı response\'da:', data);
        }
        
        return data;
        
    } catch (error) {
        console.error('Login API hatası:', error);
        // Network hatası kontrolü
        if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            throw new Error('Backend API\'ye bağlanılamadı. Lütfen API\'nin çalıştığından emin olun (port 8000).');
        }
        throw error;
    }
}

/**
 * Kullanıcı kaydı yapar
 * @param {string} full_name - Ad soyad
 * @param {string} username - Kullanıcı adı
 * @param {string} password - Şifre
 * @returns {Promise<Object>} Kullanıcı bilgisi
 */
async function registerUser(full_name, username, password) {
    try {
        // API'ye istek gönder (Backend API port 8000'de çalışıyor)
        const response = await fetch('http://localhost:8000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                full_name: full_name,
                username: username,
                password: password
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Kayıt başarısız' }));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Register API hatası:', error);
        // Network hatası kontrolü
        if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            throw new Error('Backend API\'ye bağlanılamadı. Lütfen API\'nin çalıştığından emin olun (port 8000).');
        }
        throw error;
    }
}

/**
 * Mevcut kullanıcı bilgilerini alır (token gerektirir)
 * @returns {Promise<Object>} Kullanıcı bilgisi
 */
async function getCurrentUser() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('Token bulunamadı');
        }
        
        const tokenType = localStorage.getItem('token_type') || 'bearer';
        
        // API'ye istek gönder (Backend API port 8000'de çalışıyor)
        const response = await fetch('http://localhost:8000/users/me', {
            method: 'GET',
            headers: {
                'Authorization': `${tokenType} ${token}`
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token geçersiz, temizle
                localStorage.removeItem('access_token');
                localStorage.removeItem('token_type');
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Get current user API hatası:', error);
        // Network hatası kontrolü - sessizce başarısız ol, kullanıcıyı rahatsız etme
        if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            // Token'ı temizle çünkü API'ye ulaşılamıyor
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            throw new Error('API bağlantı hatası');
        }
        throw error;
    }
}

/**
 * Kullanıcı çıkışı yapar (token'ı temizler)
 */
function logoutUser() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
}

/**
 * Kullanıcının giriş yapıp yapmadığını kontrol eder
 * @returns {boolean} Giriş yapılmışsa true
 */
function isUserLoggedIn() {
    return !!localStorage.getItem('access_token');
}

