// Path: src/cabin_app/static/js/main.js

// DOM Elements
const engDiv = document.getElementById('eng-content');
const vieDiv = document.getElementById('vie-content');
const statusDiv = document.getElementById('status');
const micSelect = document.getElementById('mic-select');
const providerSelect = document.getElementById('provider-select');
const sttSelect = document.getElementById('stt-select'); // New STT Select
const paddingSlider = document.getElementById('padding-slider');
const paddingVal = document.getElementById('padding-val');
const pauseBtn = document.getElementById('pause-btn');

let ws = null;
let isPaused = false;

// --- INITIALIZATION ---
function init() {
    // Set default provider from injected config
    if (window.CABIN_CONFIG) {
        if (window.CABIN_CONFIG.DEFAULT_PROVIDER && providerSelect) {
            providerSelect.value = window.CABIN_CONFIG.DEFAULT_PROVIDER;
        }
        if (window.CABIN_CONFIG.DEFAULT_STT && sttSelect) {
            sttSelect.value = window.CABIN_CONFIG.DEFAULT_STT;
        }
    }
    
    // Load devices and start connection
    loadDevices();
    
    // Register global shortcuts
    document.addEventListener('keydown', handleGlobalShortcuts);
}

// --- LOGIC UI SCROLL PADDING ---
if (paddingSlider) {
    paddingSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (paddingVal) paddingVal.innerText = val + "%";
        document.documentElement.style.setProperty('--scroll-padding', val + 'vh');
        scrollToBottom(engDiv);
        scrollToBottom(vieDiv);
    });
}

// --- PAUSE / RESUME LOGIC ---
function togglePause() {
    isPaused = !isPaused;
    updatePauseUI();
    
    // Send command to server
    if (ws && ws.readyState === WebSocket.OPEN) {
        const cmd = isPaused ? "pause" : "resume";
        ws.send(JSON.stringify({ command: cmd }));
    }
}

function updatePauseUI() {
    if (pauseBtn) {
        if (isPaused) {
            pauseBtn.innerText = "▶️";
            pauseBtn.classList.add("paused");
            pauseBtn.title = "Resume (Space)";
            addSystemSeparator("⏸️ Paused");
        } else {
            pauseBtn.innerText = "⏸️";
            pauseBtn.classList.remove("paused");
            pauseBtn.title = "Pause (Space)";
            addSystemSeparator("▶️ Resumed");
        }
    }
}

function handleGlobalShortcuts(e) {
    // Spacebar to toggle pause
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT") {
        e.preventDefault(); // Prevent scrolling
        togglePause();
    }
}

if (pauseBtn) {
    pauseBtn.addEventListener('click', togglePause);
}


// --- CONNECTION LOGIC ---
async function loadDevices() {
    try {
        const res = await fetch('/api/devices');
        const devices = await res.json();
        
        if (micSelect) {
            micSelect.innerHTML = '';
            const defaultOption = document.createElement('option');
            defaultOption.value = ""; 
            defaultOption.text = "⚙️ Default System Mic";
            micSelect.appendChild(defaultOption);
            
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.text = `🎤 ${device.name}`;
                micSelect.appendChild(option);
            });
        }
        
        connect(); 
    } catch (err) { 
        console.error("Error loading devices:", err); 
    }
}

function connect() {
    if (ws) ws.close();

    const deviceId = micSelect ? micSelect.value : "";
    const provider = providerSelect ? providerSelect.value : "mock";
    const sttProvider = sttSelect ? sttSelect.value : "groq"; // New Param

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Build URL with params
    const urlParams = new URLSearchParams();
    if (deviceId) urlParams.append('device_id', deviceId);
    urlParams.append('provider', provider);
    urlParams.append('stt_provider', sttProvider);

    const wsUrl = `${protocol}//${window.location.host}/ws/cabin?${urlParams.toString()}`;
    
    if (statusDiv) statusDiv.innerText = `Connecting (${provider} + ${sttProvider})...`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        if (statusDiv) {
            statusDiv.innerText = `Connected 🟢 (STT: ${sttProvider.toUpperCase()} | AI: ${provider.toUpperCase()})`;
            statusDiv.style.color = "#00ff88";
        }
        // Sync pause state on reconnect if needed, or reset
        if (isPaused) {
            ws.send(JSON.stringify({ command: "pause" }));
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'transcript') {
                appendMessage(engDiv, data.text, 'eng');
            } else if (data.type === 'translation') {
                appendMessage(vieDiv, data.text, 'vie');
            } else if (data.type === 'error') {
                appendMessage(engDiv, data.text, 'error');
            } else if (data.type === 'status') {
                // Sync status from server if needed (optional)
            }
        } catch (e) {
            console.error("Error parsing WS message:", e);
        }
    };

    ws.onclose = (e) => {
        if (statusDiv) statusDiv.innerText = `Disconnected 🔴 (${e.code})`;
    };
    
    ws.onerror = (e) => {
        console.error("WebSocket error:", e);
    };
}

// --- EVENT LISTENERS ---
if (micSelect) {
    micSelect.addEventListener('change', () => {
        addSystemSeparator(`Switching Mic`);
        connect();
    });
}

if (providerSelect) {
    providerSelect.addEventListener('change', () => {
        const newProvider = providerSelect.options[providerSelect.selectedIndex].text;
        addSystemSeparator(`Switching AI to ${newProvider}`);
        connect();
    });
}

if (sttSelect) {
    sttSelect.addEventListener('change', () => {
        const newSTT = sttSelect.options[sttSelect.selectedIndex].text;
        addSystemSeparator(`Switching STT to ${newSTT}`);
        connect();
    });
}

// --- HELPERS ---
function addSystemSeparator(text) {
    const createSeparator = (msg) => {
        const div = document.createElement('div');
        div.className = 'system-divider';
        div.innerText = msg;
        return div;
    };
    if (engDiv) {
        engDiv.appendChild(createSeparator(text));
        scrollToBottom(engDiv);
    }
    if (vieDiv) {
        vieDiv.appendChild(createSeparator(text));
        scrollToBottom(vieDiv);
    }
}

function appendMessage(container, text, className) {
    if (!container) return;
    const div = document.createElement('div');
    div.className = `message ${className}`;
    div.innerText = text;
    container.appendChild(div);
    scrollToBottom(container);
}

function scrollToBottom(container) {
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
