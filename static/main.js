const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const chatMessages = document.getElementById('chatMessages');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const charCounter = document.getElementById('charCounter');
const clearBtn = document.getElementById('clearBtn');

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    
    // Update character counter
    const length = this.value.length;
    charCounter.textContent = `${length} / 2000`;
    
    if (length > 1900) {
        charCounter.style.color = '#ff4444';
    } else {
        charCounter.style.color = '#ff69b4';
    }
});

// Handle Enter key (Shift+Enter for new line)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Add message to chat
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? '👤' : '🤖';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Format content with basic markdown support
    const formattedContent = formatMessage(content);
    messageContent.innerHTML = formattedContent;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message with basic markdown
function formatMessage(text) {
    // Convert line breaks to paragraphs
    let formatted = text.split('\n\n').map(para => {
        if (para.trim().startsWith('[') && para.includes(']')) {
            // Format song sections
            return `<p><strong style="color: #ff69b4;">${para}</strong></p>`;
        }
        return `<p>${para.replace(/\n/g, '<br>')}</p>`;
    }).join('');
    
    // Bold text
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return formatted;
}

// Show typing indicator
function showTyping() {
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

// Hide typing indicator
function hideTyping() {
    typingIndicator.style.display = 'none';
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, true);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    charCounter.textContent = '0 / 2000';
    
    // Disable input while processing
    messageInput.disabled = true;
    sendBtn.disabled = true;
    showTyping();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        hideTyping();
        
        if (data.success) {
            addMessage(data.response, false);
            
            // Add copy button if response contains lyrics
            if (data.response.includes('[Verse') || data.response.includes('[Chorus')) {
                addCopyButton();
            }
        } else {
            addMessage(`❌ Error: ${data.error}`, false);
        }
        
    } catch (error) {
        hideTyping();
        addMessage(`❌ Error: ${error.message}`, false);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
});

// Add copy button to last message
function addCopyButton() {
    const lastMessage = chatMessages.querySelector('.bot-message:last-child .message-content');
    if (!lastMessage) return;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = '📋 Copy Lyrics';
    copyBtn.onclick = function() {
        const text = lastMessage.textContent;
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = '✓ Copied!';
            copyBtn.style.background = '#4caf50';
            copyBtn.style.borderColor = '#4caf50';
            copyBtn.style.color = 'white';
            setTimeout(() => {
                copyBtn.textContent = '📋 Copy Lyrics';
                copyBtn.style.background = '';
                copyBtn.style.borderColor = '';
                copyBtn.style.color = '';
            }, 2000);
        });
    };
    
    lastMessage.appendChild(copyBtn);
}

// Clear conversation
clearBtn.addEventListener('click', async function() {
    if (!confirm('Are you sure you want to start a new conversation? This will clear all messages.')) {
        return;
    }
    
    try {
        const response = await fetch('/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Clear all messages except the initial one
            chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <p>Hello! 👋 I'm here to help you transform your precious memories into beautiful song lyrics.</p>
                        <p>Tell me about a memory or story that's special to you, and I'll help you turn it into a song. What memory would you like to write about?</p>
                    </div>
                </div>
            `;
            scrollToBottom();
        }
    } catch (error) {
        alert('Error clearing conversation: ' + error.message);
    }
});

// Focus input on load
window.addEventListener('load', function() {
    messageInput.focus();
    scrollToBottom();
});
