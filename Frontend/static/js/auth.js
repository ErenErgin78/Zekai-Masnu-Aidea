// Auth sayfaları için JavaScript - Login ve Register işlemleri

/**
 * Tema yönetimi için basit sınıf
 */
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'default';
        this.themes = ['default', 'dark', 'light'];
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.applyTheme();
    }
    
    setupElements() {
        this.themeToggle = document.getElementById('themeToggle');
    }
    
    setupEventListeners() {
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    toggleTheme() {
        const currentIndex = this.themes.indexOf(this.theme);
        const nextIndex = (currentIndex + 1) % this.themes.length;
        this.theme = this.themes[nextIndex];
        
        this.applyTheme();
        localStorage.setItem('theme', this.theme);
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        
        if (this.themeToggle) {
            const themeIcon = this.themeToggle.querySelector('.theme-icon');
            // Tema ikonları
            const themeIcons = {
                'default': '🌱', // Yeşil tema
                'dark': '🌙',    // Koyu tema
                'light': '☀️'    // Açık tema
            };
            if (themeIcon) {
                themeIcon.textContent = themeIcons[this.theme] || '🎨';
            }
            
            // Tema tooltip'i güncelle
            const themeNames = {
                'default': 'Default (Yeşil)',
                'dark': 'Dark (Siyah)',
                'light': 'Light (Açık)'
            };
            this.themeToggle.title = `Tema: ${themeNames[this.theme] || 'Bilinmiyor'}`;
        }
    }
}

/**
 * Login sayfası için işlemler
 */
class LoginManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
    }
    
    setupElements() {
        this.loginForm = document.getElementById('loginForm');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.loginBtn = document.getElementById('loginBtn');
        this.loginBtnText = document.getElementById('loginBtnText');
        this.loginBtnLoader = document.getElementById('loginBtnLoader');
    }
    
    setupEventListeners() {
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // Şifre göster/gizle toggle
        if (this.passwordToggle && this.passwordInput) {
            this.passwordToggle.addEventListener('click', () => this.togglePassword());
        }
    }
    
    togglePassword() {
        const icon = this.passwordToggle.querySelector('.eye-icon');
        if (this.passwordInput.type === 'password') {
            this.passwordInput.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            this.passwordInput.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        // Form değerlerini al
        const username = this.usernameInput?.value.trim();
        const password = this.passwordInput?.value;
        
        // Validasyon
        if (!username || !password) {
            console.error('Login hatası: Lütfen tüm alanları doldurun.');
            this.setLoading(false);
            return;
        }
        
        // Butonu devre dışı bırak ve yükleniyor göster
        this.setLoading(true);
        
        try {
            console.log('Login işlemi başlatılıyor...');
            // API'ye login isteği gönder
            const result = await loginUser(username, password);
            console.log('Login başarılı, result:', result);
            
            // Token kontrolü
            const token = localStorage.getItem('access_token');
            console.log('Token kontrolü:', token ? 'Token var' : 'Token yok');
            
            if (!token) {
                console.error('Token localStorage\'a kaydedilmedi!');
                this.setLoading(false);
                return;
            }
            
            // Başarılı - ana sayfaya yönlendir
            console.log('Ana sayfaya yönlendiriliyor...');
            // Kısa bir gecikme ile yönlendirme (bazı tarayıcılarda sorun olabiliyor)
            setTimeout(() => {
                console.log('Yönlendirme yapılıyor...');
                window.location.href = '/';
            }, 100);
            
        } catch (error) {
            // Hata mesajını konsola yazdır
            const errorMsg = error.message || 'Giriş yapılırken bir hata oluştu. Lütfen tekrar deneyin.';
            console.error('Login hatası:', errorMsg, error);
            console.error('Error stack:', error.stack);
            this.setLoading(false);
        }
    }
    
    setLoading(loading) {
        if (this.loginBtn) {
            this.loginBtn.disabled = loading;
        }
        if (this.loginBtnText) {
            this.loginBtnText.style.display = loading ? 'none' : 'inline';
        }
        if (this.loginBtnLoader) {
            this.loginBtnLoader.style.display = loading ? 'inline' : 'none';
        }
    }
}

/**
 * Register sayfası için işlemler
 */
class RegisterManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
    }
    
    setupElements() {
        this.registerForm = document.getElementById('registerForm');
        this.fullNameInput = document.getElementById('full_name');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.confirmPasswordInput = document.getElementById('confirmPassword');
        this.confirmPasswordToggle = document.getElementById('confirmPasswordToggle');
        this.registerBtn = document.getElementById('registerBtn');
        this.registerBtnText = document.getElementById('registerBtnText');
        this.registerBtnLoader = document.getElementById('registerBtnLoader');
    }
    
    setupEventListeners() {
        if (this.registerForm) {
            this.registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }
        
        // Şifre eşleşmesini kontrol et
        if (this.confirmPasswordInput) {
            this.confirmPasswordInput.addEventListener('input', () => this.validatePasswords());
        }
        if (this.passwordInput) {
            this.passwordInput.addEventListener('input', () => this.validatePasswords());
        }
        
        // Şifre göster/gizle toggle
        if (this.passwordToggle && this.passwordInput) {
            this.passwordToggle.addEventListener('click', () => this.togglePassword('password'));
        }
        if (this.confirmPasswordToggle && this.confirmPasswordInput) {
            this.confirmPasswordToggle.addEventListener('click', () => this.togglePassword('confirmPassword'));
        }
    }
    
    togglePassword(field) {
        const input = field === 'password' ? this.passwordInput : this.confirmPasswordInput;
        const toggle = field === 'password' ? this.passwordToggle : this.confirmPasswordToggle;
        
        if (input && toggle) {
            const icon = toggle.querySelector('.eye-icon');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }
    }
    
    validatePasswords() {
        const password = this.passwordInput?.value;
        const confirmPassword = this.confirmPasswordInput?.value;
        
        if (confirmPassword && password !== confirmPassword) {
            this.confirmPasswordInput.setCustomValidity('Şifreler eşleşmiyor');
        } else {
            this.confirmPasswordInput.setCustomValidity('');
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        
        // Form değerlerini al
        const fullName = this.fullNameInput?.value.trim();
        const username = this.usernameInput?.value.trim();
        const password = this.passwordInput?.value;
        const confirmPassword = this.confirmPasswordInput?.value;
        
        // Validasyon
        if (!fullName || !username || !password || !confirmPassword) {
            console.error('Register hatası: Lütfen tüm alanları doldurun.');
            this.setLoading(false);
            return;
        }
        
        if (password.length < 6) {
            console.error('Register hatası: Şifre en az 6 karakter olmalıdır.');
            this.setLoading(false);
            return;
        }
        
        if (password !== confirmPassword) {
            console.error('Register hatası: Şifreler eşleşmiyor.');
            this.setLoading(false);
            return;
        }
        
        // Butonu devre dışı bırak ve yükleniyor göster
        this.setLoading(true);
        
        try {
            // API'ye register isteği gönder
            await registerUser(fullName, username, password);
            
            // Başarılı - login sayfasına yönlendir
            window.location.href = 'login.html?registered=true';
            
        } catch (error) {
            // Hata mesajını konsola yazdır
            const errorMsg = error.message || 'Kayıt yapılırken bir hata oluştu. Lütfen tekrar deneyin.';
            console.error('Register hatası:', errorMsg, error);
            this.setLoading(false);
        }
    }
    
    setLoading(loading) {
        if (this.registerBtn) {
            this.registerBtn.disabled = loading;
        }
        if (this.registerBtnText) {
            this.registerBtnText.style.display = loading ? 'none' : 'inline';
        }
        if (this.registerBtnLoader) {
            this.registerBtnLoader.style.display = loading ? 'inline' : 'none';
        }
    }
}

// Sayfa yüklendiğinde ilgili manager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    // Tema yöneticisini başlat
    const themeManager = new ThemeManager();
    
    // Sayfa tipine göre ilgili manager'ı başlat
    if (document.getElementById('loginForm')) {
        const loginManager = new LoginManager();
    } else if (document.getElementById('registerForm')) {
        const registerManager = new RegisterManager();
    }
    
    // Kayıt başarılı mesajını konsola yazdır (eğer varsa)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        console.log('Kayıt başarılı! Giriş yapabilirsiniz.');
    }
});

