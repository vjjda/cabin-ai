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

// --- LOCAL STORAGE HELPERS ---
function saveSettings() {
    const settings = {
        // mic: micSelect.value, // Mic ID changes often, maybe better not to save strictly or handle carefully
        stt: sttSelect ? sttSelect.value : null,
        provider: providerSelect ? providerSelect.value : null,
        buffer: bufferSlider ? bufferSlider.value : null,
        padding: paddingSlider ? paddingSlider.value : null
    };
    localStorage.setItem('cabin_settings', JSON.stringify(settings));
}

function loadSavedSettings() {
    try {
        const saved = localStorage.getItem('cabin_settings');
        if (!saved) return;
        
        const s = JSON.parse(saved);
        
        if (s.stt && sttSelect) sttSelect.value = s.stt;
        if (s.provider && providerSelect) providerSelect.value = s.provider;
        if (s.buffer && bufferSlider) {
            bufferSlider.value = s.buffer;
            if (bufferVal) bufferVal.innerText = s.buffer + "s";
        }
        if (s.padding && paddingSlider) {
            paddingSlider.value = s.padding;
            if (paddingVal) paddingVal.innerText = s.padding + "%";
            document.documentElement.style.setProperty('--scroll-padding', s.padding + 'vh');
        }
    } catch (e) {
        console.error("Error loading settings", e);
    }
}


// --- INITIALIZATION ---
function init() {
    // Inject Config Defaults
    if (window.CABIN_CONFIG) {
        const cfg = window.CABIN_CONFIG;
        
        // 1. Populate Dropdowns dynamically
        if (cfg.OPTIONS) {
            populateSelect(providerSelect, cfg.OPTIONS.AI, cfg.DEFAULT_PROVIDER);
            populateSelect(sttSelect, cfg.OPTIONS.STT, cfg.DEFAULT_STT);
        }

        // Initialize Buffer Slider from Server Config
        if (cfg.BUFFER && bufferSlider) {
            const b = cfg.BUFFER;
            bufferSlider.min = b.MIN;
            bufferSlider.max = b.MAX;
            bufferSlider.step = b.STEP;
            bufferSlider.value = b.DEFAULT;
            if (bufferVal) bufferVal.innerText = b.DEFAULT + "s";
        }
    }
    
    // 2. Override with User Saved Settings (Persistence)
    loadSavedSettings();
    
    // 3. Load devices and start connection
    loadDevices();
    
    // 4. Set initial UI state
    updatePauseUI();
    
    // 5. Global Shortcuts
    document.addEventListener('keydown', handleGlobalShortcuts);
}

function populateSelect(selectEl, options, defaultValue) {
    if (!selectEl || !options) return;
    selectEl.innerHTML = '';
    options.forEach(opt => {
        const el = document.createElement('option');
        el.value = opt.id;
        el.innerText = opt.name;
        selectEl.appendChild(el);
    });
    // Set default if provided
    if (defaultValue) {
        selectEl.value = defaultValue;
    }
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

if (settingsModal) {
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) toggleModal(false);
    });
}

// Sliders Events
if (paddingSlider) {
    paddingSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (paddingVal) paddingVal.innerText = val + "%";
        document.documentElement.style.setProperty('--scroll-padding', val + 'vh');
        scrollToBottom(engDiv);
        scrollToBottom(vieDiv);
    });
    paddingSlider.addEventListener('change', saveSettings); // Save on release
}

if (bufferSlider) {
    bufferSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (bufferVal) bufferVal.innerText = val + "s";
    });
    
    bufferSlider.addEventListener('change', () => {
         saveSettings();
         console.log("Buffer changed, reconnecting...");
         connect(); 
    });
}

if (providerSelect) providerSelect.addEventListener('change', saveSettings);
if (sttSelect) sttSelect.addEventListener('change', saveSettings);


if (applyBtn) {
    applyBtn.addEventListener('click', () => {
        saveSettings(); // Save when Apply clicked
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
            pauseBtn.classList.add("paused"); 
            pauseBtn.title = "Resume (Space)";
            addSystemSeparator("⏸️ Paused");
        } else {
            pauseBtn.classList.remove("paused");
            pauseBtn.title = "Pause (Space)";
            addSystemSeparator("▶️ Resumed");
        }
    }
}

function handleGlobalShortcuts(e) {
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
            
            // Restore saved mic if exists and still valid? 
            // For now, let's keep default or user manual selection to avoid 'missing device' issues.
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
    const sttProvider = sttSelect ? sttSelect.value : "groq";
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
            statusDiv.style.color = "#81c784";
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
            statusDiv.style.color = "#e57373";
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