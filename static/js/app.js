// app.js - Main application logic for NeonizeUI

// Initialize socket.io connection
const socket = io();

// Global state
const appState = {
    connectionStatus: 'disconnected',
    contacts: [],
    groups: [],
    rules: [],
    activeTab: 'chat',
    messages: []
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Register tab navigation
    initTabNavigation();
    
    // Initialize connection manager
    initConnectionManager();
    
    // Initialize message handling
    initMessageHandling();
    
    // Initialize contacts panel
    initContactsPanel();
    
    // Initialize groups panel
    initGroupsPanel();
    
    // Initialize automation panel
    initAutomationPanel();
    
    // Load settings
    loadSettings();
    
    // Check connection status on load
    checkConnectionStatus();
    
    // Log that initialization is complete
    console.log('NeonizeUI initialized successfully');
});

// Initialize tab navigation
function initTabNavigation() {
    // Get all navigation items
    const navItems = document.querySelectorAll('.nav-item');
    
    // Add click event listener to each nav item
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Get the target tab
            const targetTab = item.getAttribute('data-tab');
            
            // Update active tab styling
            navItems.forEach(navItem => navItem.classList.remove('active'));
            item.classList.add('active');
            
            // Hide all panels
            const panels = document.querySelectorAll('.panel');
            panels.forEach(panel => panel.classList.add('hidden'));
            
            // Special handling for connection panel
            if (appState.connectionStatus !== 'connected') {
                document.getElementById('connection-panel').classList.remove('hidden');
                return;
            }
            
            // Show the target panel
            const targetPanel = document.getElementById(`${targetTab}-panel`);
            if (targetPanel) {
                targetPanel.classList.remove('hidden');
                appState.activeTab = targetTab;
            }
        });
    });
}

// Update UI based on connection status
function updateConnectionUI(status) {
    // Update global state
    appState.connectionStatus = status;
    
    // Update status indicator
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    
    statusIndicator.className = 'status-indicator';
    
    switch (status) {
        case 'connected':
            statusIndicator.classList.add('online');
            statusText.textContent = 'Connected';
            
            // Hide connection panel and show active tab
            document.getElementById('connection-panel').classList.add('hidden');
            document.getElementById(`${appState.activeTab}-panel`).classList.remove('hidden');
            
            // Enable disconnect button
            document.getElementById('disconnect-btn').disabled = false;
            break;
            
        case 'initializing':
            statusIndicator.classList.add('connecting');
            statusText.textContent = 'Connecting...';
            
            // Show connection panel
            document.getElementById('connection-panel').classList.remove('hidden');
            document.querySelectorAll('.panel:not(#connection-panel)').forEach(
                panel => panel.classList.add('hidden')
            );
            
            // Disable disconnect button
            document.getElementById('disconnect-btn').disabled = false;
            break;
            
        case 'disconnected':
        default:
            statusIndicator.classList.add('offline');
            statusText.textContent = 'Disconnected';
            
            // Show connection panel
            document.getElementById('connection-panel').classList.remove('hidden');
            document.querySelectorAll('.panel:not(#connection-panel)').forEach(
                panel => panel.classList.add('hidden')
            );
            
            // Disable disconnect button
            document.getElementById('disconnect-btn').disabled = true;
            break;
    }
}

// Check connection status from server
function checkConnectionStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateConnectionUI(data.status);
            
            // If initializing, display QR code
            if (data.status === 'initializing' && data.qr_code) {
                displayQRCode(data.qr_code);
            }
        })
        .catch(error => {
            console.error('Error checking connection status:', error);
            updateConnectionUI('disconnected');
        });
}

// Load settings from localStorage
function loadSettings() {
    // Load session path
    const sessionPath = localStorage.getItem('sessionPath') || 'whatsapp_session';
    document.getElementById('session-path').value = sessionPath;
    
    // Load auto-connect setting
    const autoConnect = localStorage.getItem('autoConnect') === 'true';
    document.getElementById('auto-connect').checked = autoConnect;
    
    // If auto-connect is enabled and we're disconnected, connect automatically
    if (autoConnect && appState.connectionStatus === 'disconnected') {
        connectToWhatsApp();
    }
    
    // Set up settings save button
    document.getElementById('save-settings').addEventListener('click', saveSettings);
}

// Save settings to localStorage
function saveSettings() {
    const sessionPath = document.getElementById('session-path').value;
    const autoConnect = document.getElementById('auto-connect').checked;
    
    localStorage.setItem('sessionPath', sessionPath);
    localStorage.setItem('autoConnect', autoConnect);
    
    // Show success notification
    alert('Settings saved successfully');
}

// Error handling function
function handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    
    // Show error message in UI
    const messageStream = document.querySelector('.message-stream');
    const errorMessage = document.createElement('div');
    errorMessage.className = 'system-message';
    errorMessage.textContent = `Error: ${error.message || 'Unknown error occurred'}`;
    messageStream.appendChild(errorMessage);
    messageStream.scrollTop = messageStream.scrollHeight;
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Export functions and state for other modules
window.neonizeUI = {
    appState,
    updateConnectionUI,
    handleError,
    formatDate
};