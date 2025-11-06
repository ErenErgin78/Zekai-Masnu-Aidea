// Yardımcı fonksiyonlar - HTML formatlama, temizleme ve diğer utility fonksiyonları

/**
 * Mesaj içeriğini formatlar (markdown -> HTML)
 * @param {string} content - Formatlanacak içerik
 * @returns {string} Formatlanmış HTML içeriği
 */
function formatMessage(content) {
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
    formatted = cleanMismatchedHtmlTags(formatted);
    
    return formatted;
}

/**
 * Eşleşmeyen HTML etiketlerini temizler
 * @param {string} html - Temizlenecek HTML içeriği
 * @returns {string} Temizlenmiş HTML içeriği
 */
function cleanMismatchedHtmlTags(html) {
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

/**
 * Bozuk HTML yapılarını temizler
 * @param {string} html - Temizlenecek HTML içeriği
 * @returns {string} Temizlenmiş HTML içeriği
 */
function cleanBrokenHtmlTags(html) {
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

/**
 * HTML karakterlerini escape eder (XSS koruması)
 * @param {string} text - Escape edilecek metin
 * @returns {string} Escape edilmiş metin
 */
function escapeHtml(text) {
    // HTML karakterlerini escape et
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Hava durumu koduna göre ikon döndürür
 * @param {string} weatherCode - Hava durumu kodu veya açıklaması
 * @returns {string} Hava durumu emoji ikonu
 */
function getWeatherIcon(weatherCode) {
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

/**
 * Kullanıcının mevcut konumunu alır (geolocation API)
 * @returns {Promise<Object|null>} Konum bilgisi {lat, lon} veya null
 */
async function getCurrentLocation() {
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

