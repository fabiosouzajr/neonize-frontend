// Initialize Socket.IO connection with reconnection options
const socket = io({
    transports: ['websocket'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    forceNew: true
});

// Log socket connection status
socket.on('connect', () => {
    console.log('Socket connected');
    // Re-check status after connection
    checkInitialStatus();
});

socket.on('disconnect', (reason) => {
    console.log('Socket disconnected:', reason);
    if (reason === 'io server disconnect') {
        // Server initiated disconnect, try to reconnect
        socket.connect();
    }
});

socket.on('connect_error', (error) => {
    console.error('Socket connection error:', error);
    // Try to reconnect with a different transport
    if (socket.io.opts.transports[0] === 'websocket') {
        console.log('Falling back to polling transport');
        socket.io.opts.transports = ['polling', 'websocket'];
    }
});

socket.on('reconnect', (attemptNumber) => {
    console.log('Socket reconnected after', attemptNumber, 'attempts');
    // Re-check status after reconnection
    checkInitialStatus();
});

socket.on('reconnect_error', (error) => {
    console.error('Socket reconnection error:', error);
});

socket.on('reconnect_failed', () => {
    console.error('Socket reconnection failed');
    alert('Connection lost. Please refresh the page.');
});

// DOM Elements
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const statusIndicator = document.getElementById('status-indicator');
const qrContainer = document.getElementById('qr-container');
const qrCode = document.getElementById('qr-code');

// Connection status handling
socket.on('connection_status', (data) => {
    console.log('Connection status update:', data);
    updateConnectionStatus(data.status);
});

// Test event handling
socket.on('test_event', (data) => {
    console.log('Test event received:', data);
});

// QR code handling
socket.on('qr_code', (data) => {
    console.log('QR code received:', data);
    if (!data.qr) {
        console.error('No QR code data received');
        return;
    }
    try {
        // Log QR code data length
        console.log('QR code data length:', data.qr.length);
        
        // Ensure QR container is visible
        qrContainer.style.display = 'block';
        qrContainer.classList.remove('d-none');
        
        // Set QR code image
        const qrDataUrl = `data:image/png;base64,${data.qr}`;
        console.log('QR code data URL created');
        
        // Create a new image to verify the data
        const testImg = new Image();
        testImg.onload = () => {
            console.log('QR code image loaded successfully');
            qrCode.src = qrDataUrl;
            qrCode.style.display = 'block';
            qrCode.style.width = '300px';
            qrCode.style.height = 'auto';
        };
        testImg.onerror = (error) => {
            console.error('Error loading QR code image:', error);
        };
        testImg.src = qrDataUrl;
        
        console.log('QR code display process completed');
    } catch (error) {
        console.error('Error displaying QR code:', error);
    }
});

// Error handling
socket.on('error', (data) => {
    console.error('Error:', data.message);
    alert('Error: ' + data.message);
});

// Update UI based on connection status
function updateConnectionStatus(status) {
    console.log('Updating connection status:', status);
    statusIndicator.textContent = status;
    statusIndicator.className = `status-${status}`;
    
    if (status === 'connected') {
        connectBtn.style.display = 'none';
        disconnectBtn.style.display = 'block';
        qrContainer.style.display = 'none';
    } else if (status === 'disconnected') {
        connectBtn.style.display = 'block';
        disconnectBtn.style.display = 'none';
        qrContainer.style.display = 'none';
    } else if (status === 'connecting') {
        qrContainer.style.display = 'block';
    }
}

// Connect button click handler
connectBtn.addEventListener('click', async () => {
    console.log('Connect button clicked');
    try {
        // Ensure socket is connected before making the request
        if (!socket.connected) {
            console.log('Socket not connected, attempting to connect...');
            socket.connect();
            // Wait for connection
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Socket connection timeout'));
                }, 5000);
                
                const checkConnection = setInterval(() => {
                    if (socket.connected) {
                        clearInterval(checkConnection);
                        clearTimeout(timeout);
                        resolve();
                    }
                }, 100);
            });
        }

        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to connect');
        }
        
        const data = await response.json();
        console.log('Connection response:', data);
    } catch (error) {
        console.error('Connection error:', error);
        alert('Failed to connect: ' + error.message);
    }
});

// Disconnect button click handler
disconnectBtn.addEventListener('click', async () => {
    console.log('Disconnect button clicked');
    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to disconnect');
        }
        
        const data = await response.json();
        console.log('Disconnection response:', data);
    } catch (error) {
        console.error('Disconnection error:', error);
        alert('Failed to disconnect: ' + error.message);
    }
});

// Initial status check
async function checkInitialStatus() {
    console.log('Checking initial status');
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        console.log('Initial status:', data);
        updateConnectionStatus(data.status);
    } catch (error) {
        console.error('Status check error:', error);
    }
}

// Check initial status when page loads
checkInitialStatus(); 