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
            typing: document.getElementById('typingIndicator')
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
            this.addBotMessage("Hi there! I'm your ASL learning assistant. How can I help you today? 👋");
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
        if (!text) return;

        // Add user message
        this.addUserMessage(text);
        this.elements.input.value = '';

        // Show typing indicator
        this.showTyping(true);

        try {
            // Simulate network delay for realism
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            this.showTyping(false);

            if (data.success) {
                this.addBotMessage(data.reply);
            } else {
                this.addBotMessage(data.message || "I'm having trouble connecting to my brain right now. Try again later! 🧠");
            }

        } catch (error) {
            console.error('Chat Error:', error);
            this.showTyping(false);
            this.addBotMessage("Sorry, I encountered a connection error. Please check your internet.");
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

        // Basic formatting (bolding)
        div.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

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
