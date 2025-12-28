/**
 * SEMI Global JavaScript Hub
 * Modernized for Premium Design System
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialization & UI Setup
    initializeAnimations();
    setupUserMenu();
    setupStatsObserver();
    setupTranslationLogic();
});

/**
 * Handle AOS-style animations and global transitions
 */
function initializeAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-aos]').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
        observer.observe(el);
    });
}

/**
 * User Profile Dropdown logic
 */
function setupUserMenu() {
    const trigger = document.getElementById('userMenuTrigger');
    const dropdown = document.getElementById('userDropdown');

    if (trigger && dropdown) {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });

        document.addEventListener('click', () => {
            dropdown.classList.remove('active');
        });
    }
}

/**
 * Numerical Stats counter animation
 */
function setupStatsObserver() {
    const statNumbers = document.querySelectorAll('.stat-number, .counter');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const text = el.textContent;
                const targetValue = parseInt(el.getAttribute('data-target') || text.replace(/\D/g, ''));
                if (isNaN(targetValue)) return;

                animateCount(el, targetValue, text.includes('+'), text.includes('%'));
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(n => observer.observe(n));
}

function animateCount(el, target, hasPlus, hasPercent) {
    let current = 0;
    const duration = 2000;
    const step = target / (duration / 16);

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            el.textContent = target.toLocaleString() + (hasPlus ? '+' : '') + (hasPercent ? '%' : '');
            clearInterval(timer);
        } else {
            el.textContent = Math.floor(current).toLocaleString();
        }
    }, 16);
}

/**
 * Unified Translation Core
 */
function setupTranslationLogic() {
    const wordInput = document.getElementById('wordInput');
    const translateBtn = document.getElementById('translateBtn');
    const outputArea = document.getElementById('output');

    if (!translateBtn || !wordInput) return;

    translateBtn.addEventListener('click', async () => {
        const text = wordInput.value.trim();
        if (!text) return;

        translateBtn.disabled = true;
        translateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        outputArea.innerHTML = '<div class="loading-state" style="text-align:center; padding: 40px; opacity: 0.6;">Generating sign sequence...</div>';

        try {
            const res = await fetch('/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await res.json();

            if (data.success && data.sign_assets) {
                renderTranslation(data.sign_assets, text);
            } else {
                outputArea.innerHTML = `<div class="glass-card" style="padding: 20px; color: #ef4444; border-color: rgba(239, 68, 68, 0.2);">${data.message || 'Translation failed'}</div>`;
            }
        } catch (e) {
            outputArea.innerHTML = '<div class="glass-card" style="padding: 20px; color: #ef4444; border-color: rgba(239, 68, 68, 0.2);">Connection error. Please check your network.</div>';
        } finally {
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<i class="fas fa-magic"></i> Translate';
        }
    });

    wordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') translateBtn.click();
    });
}

function renderTranslation(assets, originalText) {
    const output = document.getElementById('output');
    output.innerHTML = '';

    const container = document.createElement('div');
    container.className = 'translation-result';
    container.style.animation = 'fadeIn 0.5s ease-out';

    const label = document.createElement('h3');
    label.style.marginBottom = '24px';
    label.style.textAlign = 'center';
    label.style.fontSize = '1.4rem';
    label.textContent = `"${originalText}"`;
    container.appendChild(label);

    const assetGrid = document.createElement('div');
    assetGrid.style.display = 'flex';
    assetGrid.style.gap = '15px';
    assetGrid.style.flexWrap = 'wrap';
    assetGrid.style.justifyContent = 'center';

    assets.forEach(asset => {
        if (asset.type === 'break') {
            const spacer = document.createElement('div');
            spacer.style.width = '100%';
            spacer.style.height = '10px';
            assetGrid.appendChild(spacer);
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'glass-card';
        wrapper.style.padding = '12px';
        wrapper.style.textAlign = 'center';
        wrapper.style.minWidth = '100px';

        const img = document.createElement('img');
        img.src = asset.url; // Corrected to use .url from backend
        img.style.width = '120px';
        img.style.height = '120px';
        img.style.objectFit = 'cover';
        img.style.borderRadius = '8px';

        const text = document.createElement('span');
        text.style.display = 'block';
        text.style.marginTop = '8px';
        text.style.fontSize = '0.8rem';
        text.style.fontWeight = '700';
        text.style.color = 'var(--accent-primary)';
        text.textContent = (asset.word || asset.char || '').toUpperCase();

        wrapper.appendChild(img);
        wrapper.appendChild(text);
        assetGrid.appendChild(wrapper);
    });

    container.appendChild(assetGrid);
    output.appendChild(container);
}
