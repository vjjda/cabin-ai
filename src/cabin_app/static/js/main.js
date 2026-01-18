// Path: src/cabin_app/static/js/main.js

// DOM Elements
const engDiv = document.getElementById('eng-content');
const vieDiv = document.getElementById('vie-content');
const statusDiv = document.getElementById('status');
const micSelect = document.getElementById('mic-select');
const providerSelect = document.getElementById('provider-select');
const paddingSlider = document.getElementById('padding-slider');
const paddingVal = document.getElementById('padding-val');

let ws = null;

// --- INITIALIZATION ---
function init() {
    // Set default provider from injected config
    if (window.CABIN_CONFIG && window.CABIN_CONFIG.DEFAULT_PROVIDER) {
        providerSelect.value = window.CABIN_CONFIG.DEFAULT_PROVIDER;
    }
    
    // Load devices and start connection
    loadDevices();
}

// --- LOGIC UI SCROLL PADDING ---
if (paddingSlider) {
    paddingSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (paddingVal) paddingVal.innerText = val + "%";
        
        // Update CSS variable immediately
        document.documentElement.style.setProperty('--scroll-padding', val + 'vh');
        
        // Scroll to see effect
        scrollToBottom(engDiv);
        scrollToBottom(vieDiv);
    });
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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Build URL with params
    const urlParams = new URLSearchParams();
    if (deviceId) urlParams.append('device_id', deviceId);
    urlParams.append('provider', provider);

    const wsUrl = `${protocol}//${window.location.host}/ws/cabin?${urlParams.toString()}`;
    
    if (statusDiv) statusDiv.innerText = `Connecting (${provider})...`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        if (statusDiv) {
            statusDiv.innerText = `Connected 🟢 (${provider.toUpperCase()})`;
            statusDiv.style.color = "#00ff88";
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
