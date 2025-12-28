// PWA Installation and Management
// Handles service worker registration, install prompts, and offline detection

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
        this.swRegistration = null;

        this.init();
    }

    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            await this.registerServiceWorker();
        }

        // Setup install prompt
        this.setupInstallPrompt();

        // Setup online/offline detection
        this.setupOnlineDetection();

        // Setup update checker
        this.setupUpdateChecker();

        // Check if already installed
        this.checkIfInstalled();
    }

    // ============================================
    // SERVICE WORKER REGISTRATION
    // ============================================
    async registerServiceWorker() {
        try {
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js', {
                scope: '/'
            });

            console.log('✅ Service Worker registered successfully:', this.swRegistration.scope);

            // Check for updates on page load
            this.swRegistration.update();

            // Listen for updates
            this.swRegistration.addEventListener('updatefound', () => {
                const newWorker = this.swRegistration.installing;

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // New service worker available
                        this.showUpdateNotification();
                    }
                });
            });

        } catch (error) {
            console.error('❌ Service Worker registration failed:', error);
        }
    }

    // ============================================
    // INSTALL PROMPT
    // ============================================
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('💡 Install prompt available');

            // Prevent the default browser install prompt
            e.preventDefault();

            // Store the event for later use
            this.deferredPrompt = e;

            // Show custom install button/banner
            this.showInstallBanner();
        });

        // Detect when app is installed
        window.addEventListener('appinstalled', () => {
            console.log('✅ PWA installed successfully');
            this.deferredPrompt = null;
            this.hideInstallBanner();

            // Track installation
            this.trackInstallation();

            // Show success message
            if (typeof showNotifier === 'function') {
                showNotifier('SignLearn installed successfully! 🎉', 'success');
            }
        });
    }

    showInstallBanner() {
        // Check if user has dismissed the banner before
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        const dismissedTime = localStorage.getItem('pwa-install-dismissed-time');

        // Show again after 7 days
        if (dismissed && dismissedTime) {
            const daysSinceDismissal = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
            if (daysSinceDismissal < 7) {
                return;
            }
        }

        // Create install banner
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'pwa-install-banner';
        banner.innerHTML = `
            <div class="pwa-banner-content">
                <div class="pwa-banner-icon">
                    <i class="fas fa-mobile-alt"></i>
                </div>
                <div class="pwa-banner-text">
                    <h4>Install SignLearn</h4>
                    <p>Get the app experience with offline access and faster loading</p>
                </div>
                <div class="pwa-banner-actions">
                    <button id="pwa-install-btn" class="btn btn-primary btn-small">
                        <i class="fas fa-download"></i> Install
                    </button>
                    <button id="pwa-dismiss-btn" class="btn btn-outline btn-small">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // Animate in
        setTimeout(() => banner.classList.add('active'), 100);

        // Install button click
        document.getElementById('pwa-install-btn').addEventListener('click', () => {
            this.promptInstall();
        });

        // Dismiss button click
        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
            this.dismissInstallBanner();
        });
    }

    async promptInstall() {
        if (!this.deferredPrompt) {
            console.log('Install prompt not available');
            return;
        }

        // Show the install prompt
        this.deferredPrompt.prompt();

        // Wait for the user's response
        const { outcome } = await this.deferredPrompt.userChoice;

        console.log(`User response to install prompt: ${outcome}`);

        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
            this.dismissInstallBanner();
        }

        // Clear the deferred prompt
        this.deferredPrompt = null;
    }

    dismissInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('active');
            setTimeout(() => banner.remove(), 300);
        }

        // Remember dismissal
        localStorage.setItem('pwa-install-dismissed', 'true');
        localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
    }

    hideInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('active');
            setTimeout(() => banner.remove(), 300);
        }
    }

    // ============================================
    // ONLINE/OFFLINE DETECTION
    // ============================================
    setupOnlineDetection() {
        window.addEventListener('online', () => {
            console.log('🌐 Back online');
            this.isOnline = true;
            this.showOnlineNotification();
            this.updateOnlineStatus();
        });

        window.addEventListener('offline', () => {
            console.log('📡 Gone offline');
            this.isOnline = false;
            this.showOfflineNotification();
            this.updateOnlineStatus();
        });

        // Initial status
        this.updateOnlineStatus();
    }

    updateOnlineStatus() {
        const statusIndicator = document.getElementById('online-status');

        if (!statusIndicator) {
            // Create status indicator if it doesn't exist
            const indicator = document.createElement('div');
            indicator.id = 'online-status';
            indicator.className = 'online-status-indicator';
            document.body.appendChild(indicator);
        }

        const indicator = document.getElementById('online-status');

        if (this.isOnline) {
            indicator.classList.remove('offline');
            indicator.classList.add('online');
            indicator.innerHTML = '<i class="fas fa-wifi"></i> Online';
        } else {
            indicator.classList.remove('online');
            indicator.classList.add('offline');
            indicator.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline Mode';
        }

        // Auto-hide after 3 seconds if online
        if (this.isOnline) {
            setTimeout(() => {
                indicator.classList.add('hidden');
            }, 3000);
        } else {
            indicator.classList.remove('hidden');
        }
    }

    showOnlineNotification() {
        if (typeof showNotifier === 'function') {
            showNotifier('You are back online! 🌐', 'success');
        }
    }

    showOfflineNotification() {
        if (typeof showNotifier === 'function') {
            showNotifier('You are offline. Some features may be limited. 📡', 'info');
        }
    }

    // ============================================
    // UPDATE CHECKER
    // ============================================
    setupUpdateChecker() {
        // Check for updates every 30 minutes
        setInterval(() => {
            if (this.swRegistration) {
                this.swRegistration.update();
            }
        }, 30 * 60 * 1000);
    }

    showUpdateNotification() {
        // Create update notification
        const notification = document.createElement('div');
        notification.id = 'pwa-update-notification';
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div class="pwa-update-content">
                <div class="pwa-update-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                <div class="pwa-update-text">
                    <h4>Update Available</h4>
                    <p>A new version of SignLearn is available</p>
                </div>
                <button id="pwa-update-btn" class="btn btn-primary btn-small">
                    <i class="fas fa-redo"></i> Update Now
                </button>
            </div>
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('active'), 100);

        // Update button click
        document.getElementById('pwa-update-btn').addEventListener('click', () => {
            this.applyUpdate();
        });
    }

    applyUpdate() {
        if (this.swRegistration && this.swRegistration.waiting) {
            // Tell the service worker to skip waiting
            this.swRegistration.waiting.postMessage({ action: 'skipWaiting' });

            // Reload the page to activate the new service worker
            window.location.reload();
        }
    }

    // ============================================
    // INSTALLATION TRACKING
    // ============================================
    checkIfInstalled() {
        // Check if running as installed PWA
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone
            || document.referrer.includes('android-app://');

        if (isStandalone) {
            console.log('✅ Running as installed PWA');
            document.body.classList.add('pwa-installed');

            // Track in analytics
            this.trackPWAUsage();
        }
    }

    trackInstallation() {
        // Track installation event
        console.log('📊 Tracking PWA installation');

        // Send to analytics if available
        if (typeof gtag === 'function') {
            gtag('event', 'pwa_install', {
                event_category: 'engagement',
                event_label: 'PWA Installation'
            });
        }

        // Store installation date
        localStorage.setItem('pwa-installed-date', new Date().toISOString());
    }

    trackPWAUsage() {
        // Track PWA usage
        console.log('📊 Tracking PWA usage');

        if (typeof gtag === 'function') {
            gtag('event', 'pwa_usage', {
                event_category: 'engagement',
                event_label: 'PWA Active Session'
            });
        }
    }

    // ============================================
    // PUBLIC API
    // ============================================

    // Check if app can be installed
    canInstall() {
        return this.deferredPrompt !== null;
    }

    // Check if app is installed
    isInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone;
    }

    // Get online status
    getOnlineStatus() {
        return this.isOnline;
    }

    // Manually trigger install prompt
    install() {
        this.promptInstall();
    }
}

// Initialize PWA Manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pwaManager = new PWAManager();
    });
} else {
    window.pwaManager = new PWAManager();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}
