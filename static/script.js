const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatContainer = document.getElementById('chat-container');
const sendButton = document.getElementById('send-button');
const statusIndicator = document.getElementById('status-indicator');
const statusText = statusIndicator.querySelector('.status-text');

// Verify backend status periodically until ready
let isReady = false;

// Initialize mermaid
mermaid.initialize({ startOnLoad: false, theme: 'dark' });

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(role === 'user' ? 'user-message' : 'ai-message');
    
    const headerTitle = role === 'user' ? 'Tú' : 'MODELO DE NEGOCIOS IA';
    
    // Use marked.js for rich AI rendering, simple breaks for user
    let formattedContent = role === 'user' ? content.replace(/\n/g, '<br>') : marked.parse(content);
    
    msgDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">${headerTitle}</div>
            <div class="message-body">${formattedContent}</div>
        </div>
    `;
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Render Mermaid diagrams if present
    if (role === 'ai') {
        const mermaidBlocks = msgDiv.querySelectorAll('code.language-mermaid');
        mermaidBlocks.forEach((block, index) => {
            const id = `mermaid-${Date.now()}-${index}`;
            const graphDefinition = block.textContent;
            const preElement = block.parentElement;
            
            mermaid.render(id, graphDefinition).then(result => {
                const svgDiv = document.createElement('div');
                svgDiv.innerHTML = result.svg;
                svgDiv.style.backgroundColor = 'rgba(255,255,255,0.05)';
                svgDiv.style.padding = '1rem';
                svgDiv.style.borderRadius = '8px';
                svgDiv.style.marginTop = '1rem';
                preElement.replaceWith(svgDiv);
            }).catch(e => {
                console.error("Mermaid error:", e);
            });
        });
    }
}

function appendTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'ai-message');
    msgDiv.id = 'typing-indicator';
    
    msgDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">MODELO DE NEGOCIOS IA</div>
            <div class="message-body">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    // Add user message
    appendMessage('user', query);
    userInput.value = '';
    sendButton.disabled = true;
    
    appendTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        removeTypingIndicator();
        
        if (data.error) {
            appendMessage('system', 'Error: ' + data.error);
            if(data.error.includes("inicializando")) {
                isReady = false;
            }
        } else {
            appendMessage('ai', data.answer);
            isReady = true;
        }
    } catch (error) {
        removeTypingIndicator();
        appendMessage('system', 'Error de conexión. Asegúrate de que el servidor esté corriendo.');
    } finally {
        sendButton.disabled = false;
        userInput.focus();
        updateStatusUI();
    }
});

// File Upload Handler
const fileUpload = document.getElementById('file-upload');
fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    appendMessage('system', `Subiendo archivo: ${file.name}... procesando fragmentos, por favor espera.`);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.error) {
            appendMessage('system', 'Error al subir: ' + data.error);
        } else {
            appendMessage('system', data.message);
        }
    } catch (error) {
        appendMessage('system', 'Error de conexión al subir el archivo.');
    }
    
    fileUpload.value = '';
});

function updateStatusUI() {
    if (isReady) {
        statusIndicator.classList.add('ready');
        statusText.textContent = 'Sistema Listo';
    } else {
        statusIndicator.classList.remove('ready');
        statusText.textContent = 'Inicializando o Descargando Cerebro (Puede tomar varios minutos la primera vez)...';
    }
}

// Initial status check
async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.status === 'initializing') {
            isReady = false;
            setTimeout(checkStatus, 3000);
        } else {
            isReady = true;
        }
    } catch (e) {
        isReady = false;
        setTimeout(checkStatus, 3000);
    }
    updateStatusUI();
}

// Start checking status on load
setTimeout(checkStatus, 1000);
