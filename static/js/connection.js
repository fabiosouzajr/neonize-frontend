// connection.js - WhatsApp connection management

// Initialize connection management
function initConnectionManager() {
    // Set up connect button handler
    document.getElementById('connect-btn').addEventListener('click', connectToWhatsApp);
    
    // Set up disconnect button handler
    document.getElementById('disconnect-btn').addEventListener('click', disconnectFromWhatsApp);
    
    // Set up QR code refresh button handler
    document.getElementById('refresh-qr').addEventListener('click', requestQRCode);
    
    // Set up socket event handlers
    setupSocketEvents();
}

// Connect to WhatsApp
function connectToWhatsApp() {
    // Get session path from settings
    const sessionPath = document.getElementById('session-path').value;
    
    // Update UI
    window.neonizeUI.updateConnectionUI('initializing');
    
    // Send connection request to server
    fetch('/api/connect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_path: sessionPath })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Connection response:', data);
        window.neonizeUI.updateConnectionUI(data.status);
    })
    .catch(error => {
        window.neonizeUI.handleError(error, 'connecting to WhatsApp');
        window.neonizeUI.updateConnectionUI('disconnected');
    });
}

// Disconnect from WhatsApp
function disconnectFromWhatsApp() {
    // Update UI
    window.neonizeUI.updateConnectionUI('disconnected');
    
    // Send disconnect request to server
    fetch('/api/disconnect', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Disconnect response:', data);
        
        if (data.success) {
            // Show success message
            const messageStream = document.querySelector('.message-stream');
            const systemMessage = document.createElement('div');
            systemMessage.className = 'system-message';
            systemMessage.textContent = 'Disconnected from WhatsApp';
            messageStream.appendChild(systemMessage);
            messageStream.scrollTop = messageStream.scrollHeight;
        } else {
            window.neonizeUI.handleError({ message: data.message }, 'disconnecting from WhatsApp');
        }
    })
    .catch(error => {
        window.neonizeUI.handleError(error, 'disconnecting from WhatsApp');
    });
}

// Display QR code
function displayQRCode(qrData) {
    // Clear previous QR code
    const qrCodeContainer = document.getElementById('qr-code');
    qrCodeContainer.innerHTML = '';
    
    // Generate new QR code
    if (qrData) {
        new QRCode(qrCodeContainer, {
            text: qrData,
            width: 256,
            height: 256,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    }
}

// Request QR code refresh
function requestQRCode() {
    // Send request to server via Socket.IO
    socket.emit('request_qr');
}

// Set up Socket.IO event handlers
function setupSocketEvents() {
    // Connection status updates
    socket.on('connection_status', (data) => {
        console.log('Connection status update:', data);
        window.neonizeUI.updateConnectionUI(data.status);
    });
    
    // QR code updates
    socket.on('qr_code', (data) => {
        console.log('QR code received');
        displayQRCode(data.qr_data);
    });
    
    // Socket connection error
    socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        window.neonizeUI.handleError({ message: 'Connection to server lost' }, 'socket connection');
    });
    
    // Socket reconnect
    socket.on('reconnect', () => {
        console.log('Reconnected to server');
        checkConnectionStatus();
    });
}

// Make the connection functions globally available
window.connectToWhatsApp = connectToWhatsApp;
window.disconnectFromWhatsApp = disconnectFromWhatsApp;
window.requestQRCode = requestQRCode;

// Add a function to check connection status to global API
window.checkConnectionStatus = checkConnectionStatus;

// Socket.io connection
const socket = io();

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const qrContainer = document.getElementById('qr-container');
const qrCode = document.getElementById('qr-code');
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');

// Connection status handling
socket.on('connection_status', (data) => {
    updateConnectionStatus(data.status);
});

socket.on('qr_code', (data) => {
    showQRCode(data.qr);
});

socket.on('error', (data) => {
    addSystemMessage(`Error: ${data.message}`, 'error');
});

// Update connection status UI
function updateConnectionStatus(status) {
    statusIndicator.className = `status-${status}`;
    statusIndicator.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    if (status === 'connected') {
        qrContainer.classList.add('d-none');
        connectBtn.classList.add('d-none');
        disconnectBtn.classList.remove('d-none');
        loadContacts();
        loadGroups();
    } else if (status === 'disconnected') {
        qrContainer.classList.add('d-none');
        connectBtn.classList.remove('d-none');
        disconnectBtn.classList.add('d-none');
    }
}

// Show QR code for connection
function showQRCode(qrData) {
    qrCode.src = `data:image/png;base64,${qrData}`;
    qrContainer.classList.remove('d-none');
    statusIndicator.className = 'status-connecting';
    statusIndicator.textContent = 'Connecting...';
}

// Connect button click handler
connectBtn.addEventListener('click', () => {
    fetch('/api/connect', {
        method: 'POST'
    }).catch(error => {
        addSystemMessage(`Connection error: ${error}`, 'error');
    });
});

// Disconnect button click handler
disconnectBtn.addEventListener('click', () => {
    fetch('/api/disconnect', {
        method: 'POST'
    }).catch(error => {
        addSystemMessage(`Disconnection error: ${error}`, 'error');
    });
});

// Load contacts
function loadContacts() {
    fetch('/api/contacts')
        .then(response => response.json())
        .then(data => {
            const contactsList = document.getElementById('contacts-list');
            contactsList.innerHTML = '';
            data.contacts.forEach(contact => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = contact.name || contact.number;
                item.dataset.id = contact.id;
                item.addEventListener('click', () => selectContact(contact));
                contactsList.appendChild(item);
            });
        })
        .catch(error => {
            addSystemMessage(`Error loading contacts: ${error}`, 'error');
        });
}

// Load groups
function loadGroups() {
    fetch('/api/groups')
        .then(response => response.json())
        .then(data => {
            const groupsList = document.getElementById('groups-list');
            groupsList.innerHTML = '';
            data.groups.forEach(group => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = group.name;
                item.dataset.id = group.id;
                item.addEventListener('click', () => selectGroup(group));
                groupsList.appendChild(item);
            });
        })
        .catch(error => {
            addSystemMessage(`Error loading groups: ${error}`, 'error');
        });
}

// Add system message to the message stream
function addSystemMessage(message, type) {
    const messageStream = document.getElementById('message-stream');
    const messageElement = document.createElement('div');
    messageElement.className = `message message-type-${type}`;
    messageElement.textContent = message;
    messageStream.appendChild(messageElement);
    messageStream.scrollTop = messageStream.scrollHeight;
}