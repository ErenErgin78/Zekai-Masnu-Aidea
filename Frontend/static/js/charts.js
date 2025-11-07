// Grafik fonksiyonları - Weather ve Soil grafikleri

/**
 * Hava durumu 24 saatlik grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {Object} weatherData - Hava durumu verileri
 */
function createWeatherChart(umayChatInstance, weatherData) {
    const ctx = document.getElementById('weatherChart');
    if (!ctx) return;
    
    // 24 saatlik veri oluştur (günlük verilerden interpolasyon)
    const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
    
    // Sıcaklık verileri - günlük ortalama sıcaklıktan interpolasyon
    const baseTemp = weatherData.temperature || 20;
    const minTemp = weatherData.apparent_temperature_min || baseTemp - 5;
    const maxTemp = weatherData.apparent_temperature_max || baseTemp + 5;
    
    // Gün içi sıcaklık dağılımı (sabah düşük, öğlen yüksek, akşam düşük)
    const temperatures = hours.map((_, i) => {
        const hour = i;
        let temp;
        if (hour >= 6 && hour <= 14) {
            // Sabah 6'dan öğlen 14'e kadar artış
            const progress = (hour - 6) / 8;
            temp = minTemp + (maxTemp - minTemp) * progress;
        } else if (hour > 14 && hour <= 20) {
            // Öğleden sonra 14'ten akşam 20'ye kadar düşüş
            const progress = (hour - 14) / 6;
            temp = maxTemp - (maxTemp - minTemp) * progress * 0.7;
        } else {
            // Gece ve sabah erken saatler
            temp = minTemp + (baseTemp - minTemp) * 0.3;
        }
        return Math.round(temp);
    });
    
    // Yağış verileri - günlük toplam yağıştan interpolasyon
    const totalPrecipitation = weatherData.precipitation_sum || 0;
    
    // Eğer toplam yağış 0 ise, tüm saatlerde 0 göster
    // Eğer toplam yağış varsa, bunu 24 saate gerçekçi bir şekilde dağıt
    const precipitation = hours.map((_, i) => {
        const hour = i;
        if (totalPrecipitation === 0) return 0;
        
        // Yağış genellikle sabah (6-9) ve akşam (18-21) saatlerinde daha fazla olur
        // Dağılım oranları (toplam ~%100 olacak şekilde ayarlanmış)
        let distribution = 0.025; // Varsayılan dağılım (%2.5)
        if ((hour >= 6 && hour <= 9) || (hour >= 18 && hour <= 21)) {
            distribution = 0.06; // Sabah ve akşam saatlerinde daha fazla (%6)
        } else if (hour >= 12 && hour <= 15) {
            distribution = 0.015; // Öğlen saatlerinde daha az (%1.5)
        }
        
        // Toplam yağışı dağılım oranına göre hesapla
        return Math.max(0, totalPrecipitation * distribution);
    });
    
    if (umayChatInstance.charts.weatherChart) {
        umayChatInstance.charts.weatherChart.destroy();
    }
    
    umayChatInstance.charts.weatherChart = new Chart(ctx, {
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
                    ticks: { 
                        color: '#A0A0A0', 
                        font: { size: 9 },
                        callback: function(value) {
                            return value + '°C';
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Yağış çizgi grafiğini oluşturur (24 saatlik)
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {Object} weatherData - Hava durumu verileri
 */
function createPrecipitationLineChart(umayChatInstance, weatherData) {
    const ctx = document.getElementById('precipitationLineChart');
    if (!ctx) return;
    
    // 24 saatlik veri oluştur (günlük verilerden interpolasyon)
    const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
    
    // Yağış verileri - günlük toplam yağıştan interpolasyon
    const totalPrecipitation = weatherData.precipitation_sum || 0;
    
    // Eğer toplam yağış 0 ise, tüm saatlerde 0 göster
    // Eğer toplam yağış varsa, bunu 24 saate gerçekçi bir şekilde dağıt
    const precipitation = hours.map((_, i) => {
        const hour = i;
        if (totalPrecipitation === 0) return 0;
        
        // Yağış genellikle sabah (6-9) ve akşam (18-21) saatlerinde daha fazla olur
        // Dağılım oranları (toplam ~%100 olacak şekilde ayarlanmış)
        let distribution = 0.025; // Varsayılan dağılım (%2.5)
        if ((hour >= 6 && hour <= 9) || (hour >= 18 && hour <= 21)) {
            distribution = 0.06; // Sabah ve akşam saatlerinde daha fazla (%6)
        } else if (hour >= 12 && hour <= 15) {
            distribution = 0.015; // Öğlen saatlerinde daha az (%1.5)
        }
        
        // Toplam yağışı dağılım oranına göre hesapla
        return Math.max(0, totalPrecipitation * distribution);
    });
    
    // Eski grafiği temizle
    if (umayChatInstance.charts.precipitationLineChart) {
        umayChatInstance.charts.precipitationLineChart.destroy();
    }
    
    umayChatInstance.charts.precipitationLineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.filter((_, i) => i % 3 === 0), // Her 3 saatte bir göster
            datasets: [
                {
                    label: 'Yağış (mm)',
                    data: precipitation.filter((_, i) => i % 3 === 0),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
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
                    beginAtZero: true,
                    ticks: { 
                        color: '#A0A0A0', 
                        font: { size: 9 },
                        callback: function(value) {
                            return value + ' mm';
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Hissedilen sıcaklık grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {Object} weatherData - Hava durumu verileri
 */
function createApparentTemperatureChart(umayChatInstance, weatherData) {
    const ctx = document.getElementById('apparentTemperatureChart');
    if (!ctx) return;
    
    // Hissedilen sıcaklık değerlerini al
    const minTemp = weatherData.apparent_temperature_min ? Math.round(weatherData.apparent_temperature_min) : 0;
    const meanTemp = weatherData.apparent_temperature_mean ? Math.round(weatherData.apparent_temperature_mean) : 0;
    const maxTemp = weatherData.apparent_temperature_max ? Math.round(weatherData.apparent_temperature_max) : 0;
    
    // Eski grafiği temizle
    if (umayChatInstance.charts.apparentTemperatureChart) {
        umayChatInstance.charts.apparentTemperatureChart.destroy();
    }
    
    umayChatInstance.charts.apparentTemperatureChart = new Chart(ctx, {
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

/**
 * Yağış grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {Object} weatherData - Hava durumu verileri
 */
function createPrecipitationChart(umayChatInstance, weatherData) {
    const ctx = document.getElementById('precipitationChart');
    if (!ctx) return;
    
    // Yağış değerlerini al
    const rainSum = weatherData.rain_sum != null ? weatherData.rain_sum : 0;
    const showersSum = weatherData.showers_sum != null ? weatherData.showers_sum : 0;
    const snowfallSum = weatherData.snowfall_sum != null ? weatherData.snowfall_sum : 0;
    const precipitationSum = weatherData.precipitation_sum != null ? weatherData.precipitation_sum : 0;
    
    // Eski grafiği temizle
    if (umayChatInstance.charts.precipitationChart) {
        umayChatInstance.charts.precipitationChart.destroy();
    }
    
    umayChatInstance.charts.precipitationChart = new Chart(ctx, {
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

/**
 * Rüzgar grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {Object} weatherData - Hava durumu verileri
 */
function createWindChart(umayChatInstance, weatherData) {
    const ctx = document.getElementById('windChart');
    if (!ctx) return;
    
    // Rüzgar değerlerini al
    const windSpeedMax = weatherData.wind_speed_max || 0;
    const windGustsMax = weatherData.wind_gusts_max || 0;
    
    // Eski grafiği temizle
    if (umayChatInstance.charts.windChart) {
        umayChatInstance.charts.windChart.destroy();
    }
    
    umayChatInstance.charts.windChart = new Chart(ctx, {
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

/**
 * pH gauge grafiğini oluşturur (canvas drawing)
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} pHValue - pH değeri
 */
function createPHGauge(umayChatInstance, pHValue) {
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

/**
 * Toprak bileşimi grafiğini oluşturur (doughnut chart)
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} clay - Kil yüzdesi
 * @param {number} silt - Silt yüzdesi
 * @param {number} sand - Kum yüzdesi
 */
function createSoilCompositionChart(umayChatInstance, clay, silt, sand) {
    const ctx = document.getElementById('soilCompositionChart');
    if (!ctx) return;
    
    const total = clay + silt + sand;
    if (total === 0) return;
    
    if (umayChatInstance.charts.soilCompositionChart) {
        umayChatInstance.charts.soilCompositionChart.destroy();
    }
    
    umayChatInstance.charts.soilCompositionChart = new Chart(ctx, {
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

/**
 * Toprak yoğunluk grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} bulkDensity - Mevcut yoğunluk
 * @param {number} refBulkDensity - Referans yoğunluk
 */
function createSoilDensityChart(umayChatInstance, bulkDensity, refBulkDensity) {
    const ctx = document.getElementById('soilDensityChart');
    if (!ctx) return;
    
    if (umayChatInstance.charts.soilDensityChart) {
        umayChatInstance.charts.soilDensityChart.destroy();
    }
    
    umayChatInstance.charts.soilDensityChart = new Chart(ctx, {
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

/**
 * Organik madde ve azot grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} organicCarbon - Organik karbon yüzdesi
 * @param {number} totalNitrogen - Toplam azot yüzdesi
 */
function createSoilOrganicChart(umayChatInstance, organicCarbon, totalNitrogen) {
    const ctx = document.getElementById('soilOrganicChart');
    if (!ctx) return;
    
    if (umayChatInstance.charts.soilOrganicChart) {
        umayChatInstance.charts.soilOrganicChart.destroy();
    }
    
    umayChatInstance.charts.soilOrganicChart = new Chart(ctx, {
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

/**
 * Katyon değişim kapasitesi grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} cec - CEC değeri
 * @param {number} clayCEC - Kil CEC değeri
 * @param {number} effectiveCEC - Etkili CEC değeri
 */
function createSoilCECChart(umayChatInstance, cec, clayCEC, effectiveCEC) {
    const ctx = document.getElementById('soilCECChart');
    if (!ctx) return;
    
    if (umayChatInstance.charts.soilCECChart) {
        umayChatInstance.charts.soilCECChart.destroy();
    }
    
    umayChatInstance.charts.soilCECChart = new Chart(ctx, {
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

/**
 * Doygunluk değerleri grafiğini oluşturur
 * @param {Object} umayChatInstance - UmayChat instance'ı
 * @param {number} baseSat - Baz doygunluğu
 * @param {number} aluminumSat - Alüminyum doygunluğu
 * @param {number} sodiumPct - Değişebilir sodyum yüzdesi
 */
function createSoilSaturationChart(umayChatInstance, baseSat, aluminumSat, sodiumPct) {
    const ctx = document.getElementById('soilSaturationChart');
    if (!ctx) return;
    
    if (umayChatInstance.charts.soilSaturationChart) {
        umayChatInstance.charts.soilSaturationChart.destroy();
    }
    
    umayChatInstance.charts.soilSaturationChart = new Chart(ctx, {
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

