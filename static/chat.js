/* SEMI AI Chat Logic */

class AIChat {
    constructor() {
        this.isOpen = false;
        this.elements = {
            trigger: document.getElementById('chatTrigger'),
            window: document.getElementById('chatWindow'),
            closeBtn: document.getElementById('closeChat'),
            messages: document.getElementById('chatMessages'),
            input: document.getElementById('chatInput'),
            sendBtn: document.getElementById('sendMessage'),
            typing: document.getElementById('typingIndicator'),
            status: document.getElementById('assistantStatus')
        };

        this.init();
    }

    init() {
        // Event Listeners
        this.elements.trigger.addEventListener('click', () => this.toggleChat());
        this.elements.closeBtn.addEventListener('click', () => this.toggleChat());
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Add initial greeting if empty
        if (this.elements.messages.children.length === 1) { // 1 is typing indicator
            this.addBotMessage("Hi there! I'm your SEMI Sign Language Assistant. How can I help you today? 👋");
        }
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        this.elements.window.classList.toggle('active', this.isOpen);

        // Hide trigger when open on mobile
        if (window.innerWidth <= 480) {
            this.elements.trigger.style.display = this.isOpen ? 'none' : 'flex';
        }

        if (this.isOpen) {
            this.elements.input.focus();
            this.scrollToBottom();
        }
    }

    async sendMessage() {
        const text = this.elements.input.value.trim();
        if (!text || this.sending) return;
        this.sending = true;

        // Add user message
        this.addUserMessage(text);
        this.elements.input.value = '';

        // Show typing indicator
        this.showTyping(true);

        try {
            // Provider availability is learned from this response.
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            this.showTyping(false);

            if (data.status) {
                const labels = {
                    available: 'AI available',
                    unavailable: 'AI unavailable - limited responses',
                    unconfigured: 'Limited local responses'
                };
                this.elements.status.textContent = labels[data.status] || 'Status unknown';
            }
            if (data.success) {
                this.addBotMessage((data.mode === 'ai' ? 'AI response: ' : '') + data.reply);
            } else {
                this.addBotMessage(data.message || "The assistant is temporarily unavailable. Please try again.");
            }

        } catch (error) {
            this.elements.status.textContent = 'Connection unavailable';
            this.showTyping(false);
            this.addBotMessage("Sorry, I encountered a connection error. Please try again.");
        } finally {
            this.sending = false;
        }
    }

    addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user';
        div.textContent = text;
        this.elements.messages.insertBefore(div, this.elements.typing);
        this.scrollToBottom();
    }

    addBotMessage(text) {
        const div = document.createElement('div');
        div.className = 'message bot';

        // Render responses as text, never executable HTML.
        div.textContent = text.replace(/\*\*(.*?)\*\*/g, '$1');

        this.elements.messages.insertBefore(div, this.elements.typing);
        this.scrollToBottom();
    }

    showTyping(show) {
        this.elements.typing.classList.toggle('active', show);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiChat = new AIChat();
});
