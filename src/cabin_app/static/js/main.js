// Path: src/cabin_app/static/js/main.js

// DOM Elements
const engDiv = document.getElementById('eng-content');
const vieDiv = document.getElementById('vie-content');
const statusDiv = document.getElementById('status');

// Settings Elements
const micSelect = document.getElementById('mic-select');
const providerSelect = document.getElementById('provider-select');
const sttSelect = document.getElementById('stt-select');
const bufferSlider = document.getElementById('buffer-slider');
const bufferVal = document.getElementById('buffer-val');
const paddingSlider = document.getElementById('padding-slider');
const paddingVal = document.getElementById('padding-val');

// Controls
const pauseBtn = document.getElementById('pause-btn');
const settingsToggle = document.getElementById('settings-toggle');
const settingsModal = document.getElementById('settings-modal');
const closeSettings = document.getElementById('close-settings');
const applyBtn = document.getElementById('apply-btn');

let ws = null;
let isPaused = true; // Start Paused

// --- INITIALIZATION ---
function init() {
    // Inject Config Defaults
    if (window.CABIN_CONFIG) {
        if (window.CABIN_CONFIG.DEFAULT_PROVIDER && providerSelect) {
            providerSelect.value = window.CABIN_CONFIG.DEFAULT_PROVIDER;
        }
        if (window.CABIN_CONFIG.DEFAULT_STT && sttSelect) {
            sttSelect.value = window.CABIN_CONFIG.DEFAULT_STT;
        }
        // Initialize Buffer Slider
        if (window.CABIN_CONFIG.BUFFER && bufferSlider) {
            const b = window.CABIN_CONFIG.BUFFER;
            bufferSlider.min = b.MIN;
            bufferSlider.max = b.MAX;
            bufferSlider.step = b.STEP;
            bufferSlider.value = b.DEFAULT;
            if (bufferVal) bufferVal.innerText = b.DEFAULT + "s";
        }
    }
    
    // Load devices and start connection
    loadDevices();
    
    // Set initial UI state
    updatePauseUI();
    
    // Global Shortcuts
    document.addEventListener('keydown', handleGlobalShortcuts);
}

// --- UI LOGIC (Modal, Sliders) ---
function toggleModal(show) {
    if (show) {
        settingsModal.classList.remove('hidden');
    } else {
        settingsModal.classList.add('hidden');
    }
}

if (settingsToggle) settingsToggle.addEventListener('click', () => toggleModal(true));
if (closeSettings) closeSettings.addEventListener('click', () => toggleModal(false));

// Close modal when clicking outside
if (settingsModal) {
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) toggleModal(false);
    });
}

// Sliders
if (paddingSlider) {
    paddingSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (paddingVal) paddingVal.innerText = val + "%";
        document.documentElement.style.setProperty('--scroll-padding', val + 'vh');
        scrollToBottom(engDiv);
        scrollToBottom(vieDiv);
    });
}

if (bufferSlider) {
    bufferSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (bufferVal) bufferVal.innerText = val + "s";
    });
    
    // Send updated buffer config immediately when sliding stops? 
    // Currently, we only apply on connect.
    // For now, user has to reconnect to apply buffer changes effectively as it's an init param.
    // Let's add a "Reconnecting..." hint or auto-reconnect logic if desired later.
    // For now, simple UI update.
    bufferSlider.addEventListener('change', () => {
         // Auto reconnect when buffer changes for seamless UX
         console.log("Buffer changed, reconnecting...");
         connect(); 
    });
}

if (applyBtn) {
    applyBtn.addEventListener('click', () => {
        toggleModal(false);
        addSystemSeparator("Applying Settings & Reconnecting...");
        connect();
    });
}


// --- PAUSE / RESUME LOGIC ---
function togglePause() {
    isPaused = !isPaused;
    updatePauseUI();
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        const cmd = isPaused ? "pause" : "resume";
        ws.send(JSON.stringify({ command: cmd }));
    }
}

function updatePauseUI() {
    if (pauseBtn) {
        if (isPaused) {
            pauseBtn.classList.add("paused"); // Shows Play Icon via CSS
            pauseBtn.title = "Resume (Space)";
            addSystemSeparator("⏸️ Paused");
        } else {
            pauseBtn.classList.remove("paused"); // Shows Pause Icon via CSS
            pauseBtn.title = "Pause (Space)";
            addSystemSeparator("▶️ Resumed");
        }
    }
}

function handleGlobalShortcuts(e) {
    // Only toggle if modal is hidden
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT") {
        if (settingsModal && settingsModal.classList.contains('hidden')) {
            e.preventDefault();
            togglePause();
        }
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

    // Gather Params
    const deviceId = micSelect ? micSelect.value : "";
    const provider = providerSelect ? providerSelect.value : "mock";
    const sttProvider = sttSelect ? sttSelect.value : "groq";
    // JS reads '3.0' from HTML default if not moved yet
    const bufferSize = bufferSlider ? bufferSlider.value : "3.0"; 

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    const urlParams = new URLSearchParams();
    if (deviceId) urlParams.append('device_id', deviceId);
    urlParams.append('provider', provider);
    urlParams.append('stt_provider', sttProvider);
    urlParams.append('buffer', bufferSize);

    const wsUrl = `${protocol}//${window.location.host}/ws/cabin?${urlParams.toString()}`;
    
    if (statusDiv) statusDiv.innerText = `Connecting...`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        if (statusDiv) {
            statusDiv.innerText = `Online 🟢 (${sttProvider.toUpperCase()} | ${bufferSize}s)`;
            statusDiv.style.color = "#81c784"; // Muted Green
        }
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
            }
        } catch (e) {
            console.error(e);
        }
    };

    ws.onclose = (e) => {
        if (statusDiv) {
            statusDiv.innerText = `Offline 🔴`;
            statusDiv.style.color = "#e57373"; // Muted Red
        }
    };
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

document.addEventListener('DOMContentLoaded', init);
