/**
 * Chatbot Lab — Agent vs LLM
 * Chuyển đổi giữa ReAct Agent (POST /agent) và LLM Direct (POST /llm)
 */

const API_BASE_URL = 'http://localhost:8000';

// ========================================
// DOM Elements
// ========================================
const messagesContainer = document.getElementById('messagesContainer');
const messagesList = document.getElementById('messagesList');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const newChatBtn = document.getElementById('newChatBtn');
const menuBtn = document.getElementById('menuBtn');
const sidebar = document.querySelector('.sidebar');
const welcomeAgent = document.getElementById('welcomeAgent');
const welcomeLLM = document.getElementById('welcomeLLM');
const inputHint = document.getElementById('inputHint');

// Mode buttons (sidebar + topbar)
const sidebarModeBtns = document.querySelectorAll('.sidebar .mode-btn');
const topbarModeBtns = document.querySelectorAll('.topbar-mode-btn');

// ========================================
// State
// ========================================
let currentMode = 'agent'; // 'agent' | 'llm'
let isProcessing = false;

// Chat history riêng cho mỗi mode
let chatSessions = {
  agent: [],   // [{ role, content }]
  llm: [],     // [{ role, content }]
};

// ========================================
// Mode Switching
// ========================================

function switchMode(mode) {
  if (mode === currentMode) return;
  currentMode = mode;

  // Update active state trên cả sidebar + topbar
  [...sidebarModeBtns, ...topbarModeBtns].forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });

  // Swap welcome screen
  if (chatSessions[mode].length === 0) {
    welcomeAgent.style.display = mode === 'agent' ? 'flex' : 'none';
    welcomeLLM.style.display = mode === 'llm' ? 'flex' : 'none';
    messagesList.innerHTML = '';
  }

  // Update placeholder + hint
  if (mode === 'agent') {
    messageInput.placeholder = 'Nhập tin nhắn cho ReAct Agent...';
    inputHint.textContent = 'ReAct Agent — suy luận đa bước, gọi tool tự động.';
  } else {
    messageInput.placeholder = 'Nhập tin nhắn trực tiếp đến LLM...';
    inputHint.textContent = 'LLM Direct — gọi thẳng provider, không qua Agent.';
  }

  // Nếu mode đã có tin nhắn → render lại
  if (chatSessions[mode].length > 0) {
    renderMessages(mode);
  }

  messageInput.focus();
}

// Sidebar mode buttons
sidebarModeBtns.forEach(btn => {
  btn.addEventListener('click', () => switchMode(btn.dataset.mode));
});

// Topbar mode buttons
topbarModeBtns.forEach(btn => {
  btn.addEventListener('click', () => switchMode(btn.dataset.mode));
});

// ========================================
// Event Listeners
// ========================================

messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
  sendBtn.disabled = messageInput.value.trim() === '';
});

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled && !isProcessing) sendMessage();
  }
});

sendBtn.addEventListener('click', () => {
  if (!isProcessing) sendMessage();
});

// Suggestion cards
document.querySelectorAll('.suggestion-card').forEach(card => {
  card.addEventListener('click', () => {
    messageInput.value = card.getAttribute('data-prompt');
    sendMessage();
  });
});

newChatBtn.addEventListener('click', newChat);
clearBtn.addEventListener('click', newChat);

if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    toggleOverlay();
  });
}

// ========================================
// Core Functions
// ========================================

function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || isProcessing) return;

  // Ẩn welcome
  welcomeAgent.style.display = 'none';
  welcomeLLM.style.display = 'none';

  // Lưu vào session
  chatSessions[currentMode].push({ role: 'user', content: text });

  // Render user message
  appendMessageBubble(text, 'user');

  // Clear input
  messageInput.value = '';
  messageInput.style.height = 'auto';
  sendBtn.disabled = true;
  isProcessing = true;

  // Gọi API tương ứng
  if (currentMode === 'agent') {
    callAgentAPI(text);
  } else {
    callLLMAPI(text);
  }
}

// ========================================
// API Calls
// ========================================

async function callAgentAPI(userInput) {
  showTyping('🤖');

  try {
    const res = await fetch(`${API_BASE_URL}/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: userInput }),
    });

    hideTyping();
    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();

    // Parse thinking steps nếu có
    let thinkingSteps = null;
    if (data.steps && Array.isArray(data.steps)) {
      thinkingSteps = data.steps.map(s => ({
        icon: s.type === 'thought' ? '💭' : s.type === 'action' ? '⚡' : '👀',
        label: s.type === 'thought' ? 'Thought' : s.type === 'action' ? 'Action' : 'Observation',
        text: s.content || s.text || '',
      }));
    }

    const answer = data.answer || data.response || data.output || data.result || 'Không có phản hồi.';
    chatSessions.agent.push({ role: 'assistant', content: answer });
    appendMessageBubble(answer, 'bot', { thinkingSteps });

  } catch (err) {
    hideTyping();
    showError(err);
  } finally {
    done();
  }
}

async function callLLMAPI(userInput) {
  showTyping('⚡');

  // Gửi history (trừ message vừa push)
  const history = chatSessions.llm.slice(0, -1);

  try {
    const res = await fetch(`${API_BASE_URL}/llm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: userInput }),
    });

    hideTyping();
    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    const answer = data.response || data.answer || data.output || data.content || data.text || 'Không có phản hồi.';

    chatSessions.llm.push({ role: 'assistant', content: answer });
    appendMessageBubble(answer, 'bot');

  } catch (err) {
    hideTyping();
    showError(err);
  } finally {
    done();
  }
}

// ========================================
// Render Functions
// ========================================

function appendMessageBubble(content, type, extra = null) {
  const div = document.createElement('div');
  div.className = `message ${type}`;

  const time = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  const avatar = type === 'bot' ? (currentMode === 'agent' ? '🤖' : '⚡') : 'G';

  let stepsHTML = '';
  if (extra?.thinkingSteps) {
    stepsHTML = `<div class="thinking-steps">
      ${extra.thinkingSteps.map(s => `
        <div class="thinking-step">
          <span class="step-icon">${s.icon}</span>
          <span class="step-label">${s.label}</span>
          <span>${escapeHTML(s.text)}</span>
        </div>
      `).join('')}
    </div>`;
  }

  div.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <div class="message-bubble">${stepsHTML}${formatContent(content)}</div>
      <div class="message-time">${time}</div>
      ${type === 'bot' ? `
        <div class="message-actions">
          <button class="msg-action-btn" title="Sao chép" onclick="copyMessage(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
      ` : ''}
    </div>
  `;

  messagesList.appendChild(div);
  scrollToBottom();
}

function renderMessages(mode) {
  messagesList.innerHTML = '';
  const avatar = mode === 'agent' ? '🤖' : '⚡';

  chatSessions[mode].forEach(msg => {
    const type = msg.role === 'user' ? 'user' : 'bot';
    const div = document.createElement('div');
    div.className = `message ${type}`;
    const displayAvatar = type === 'bot' ? avatar : 'G';

    div.innerHTML = `
      <div class="message-avatar">${displayAvatar}</div>
      <div class="message-content">
        <div class="message-bubble">${formatContent(msg.content)}</div>
      </div>
    `;
    messagesList.appendChild(div);
  });

  scrollToBottom();
}

function showTyping(icon) {
  const div = document.createElement('div');
  div.className = 'message bot';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="message-avatar">${icon}</div>
    <div class="message-content">
      <div class="message-bubble">
        <div class="typing-indicator"><span></span><span></span><span></span></div>
      </div>
    </div>
  `;
  messagesList.appendChild(div);
  scrollToBottom();
}

function hideTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.remove();
}

function showError(err) {
  console.error('API Error:', err);
  const endpoint = currentMode === 'agent' ? '/agent' : '/llm';
  appendMessageBubble(
    `<p style="color:#ef4444;"><strong>⚠️ Lỗi kết nối</strong></p>
     <p>Không thể kết nối đến <code>POST ${API_BASE_URL}${endpoint}</code>.</p>
     <ul>
       <li>Backend server đã chạy chưa?</li>
       <li>Endpoint <code>POST ${endpoint}</code> có tồn tại không?</li>
       <li>CORS đã được bật trên backend chưa?</li>
     </ul>
     <p style="color:#6b6b6b;font-size:12px;">${err.message}</p>`,
    'bot'
  );
}

function done() {
  isProcessing = false;
  sendBtn.disabled = messageInput.value.trim() === '';
}

function newChat() {
  chatSessions[currentMode] = [];
  messagesList.innerHTML = '';
  if (currentMode === 'agent') {
    welcomeAgent.style.display = 'flex';
    welcomeLLM.style.display = 'none';
  } else {
    welcomeAgent.style.display = 'none';
    welcomeLLM.style.display = 'flex';
  }
  isProcessing = false;
  messageInput.value = '';
  messageInput.style.height = 'auto';
  sendBtn.disabled = true;
  messageInput.focus();
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ========================================
// Utility
// ========================================

function formatContent(text) {
  if (!text) return '';
  let h = text;
  h = h.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\n/g, '<br/>');
  return h;
}

function escapeHTML(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function copyMessage(btn) {
  const bubble = btn.closest('.message-content').querySelector('.message-bubble');
  navigator.clipboard.writeText(bubble.innerText).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  });
}

function toggleOverlay() {
  let overlay = document.querySelector('.sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }
  overlay.classList.toggle('show');
}

// ========================================
// Init
// ========================================
messageInput.focus();
