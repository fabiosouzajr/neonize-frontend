// messages.js - Message handling for WhatsApp

// Initialize message handling
function initMessageHandling() {
    // Set up send message button handler
    document.getElementById('send-message').addEventListener('click', sendMessage);
    
    // Set up message input enter key handler
    document.getElementById('message-text').addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Set up clear messages button handler
    document.getElementById('clear-messages').addEventListener('click', clearMessages);
    
    // Set up socket event handlers for messages
    setupMessageSocketEvents();
    
    // Load message history on init
    loadMessageHistory();
}

// Send a message
function sendMessage() {
    // Get recipient and message text
    const recipientSelect = document.getElementById('recipient-select');
    const messageInput = document.getElementById('message-text');
    
    const recipientId = recipientSelect.value;
    const messageText = messageInput.value.trim();
    
    // Validate inputs
    if (!recipientId) {
        alert('Please select a recipient');
        return;
    }
    
    if (!messageText) {
        alert('Please enter a message');
        return;
    }
    
    // Clear message input
    messageInput.value = '';
    
    // Add message to UI immediately (optimistic UI update)
    addMessageToUI({
        id: 'pending-' + Date.now(),
        chat_id: recipientId,
        sender: 'You',
        text: messageText,
        timestamp: new Date().toISOString(),
        is_outgoing: true,
        type: 'text',
        is_group: false, // We don't know this yet, but will be updated if needed
        pending: true // Mark as pending until confirmed
    });
    
    // Send message to server
    fetch('/api/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            recipient_id: recipientId,
            message: messageText
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Message send response:', data);
        
        // If failed, show error
        if (!data.success) {
            window.neonizeUI.handleError({ message: data.message }, 'sending message');
        }
    })
    .catch(error => {
        window.neonizeUI.handleError(error, 'sending message');
    });
}

// Add a message to the UI
function addMessageToUI(message) {
    const messageStream = document.querySelector('.message-stream');
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${message.is_outgoing ? 'outgoing' : 'incoming'} type-${message.type || 'text'}`;
    messageEl.id = `message-${message.id}`;
    
    // Message content
    let messageContent = '';
    
    // Add sender info for incoming group messages
    if (message.is_group && !message.is_outgoing) {
        messageContent += `<div class="sender">${message.sender}</div>`;
    }
    
    // Add message text
    messageContent += `<div class="text">${escapeHtml(message.text)}</div>`;
    
    // Add timestamp
    messageContent += `<div class="time">${window.neonizeUI.formatDate(message.timestamp)}</div>`;
    
    // Set message content
    messageEl.innerHTML = messageContent;
    
    // Add pending status if applicable
    if (message.pending) {
        messageEl.classList.add('pending');
    }
    
    // Add to message stream
    messageStream.appendChild(messageEl);
    
    // Scroll to bottom
    messageStream.scrollTop = messageStream.scrollHeight;
    
    // Add to messages array
    window.neonizeUI.appState.messages.push(message);
}

// Add a system message to the UI
function addSystemMessageToUI(text) {
    const messageStream = document.querySelector('.message-stream');
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = 'system-message';
    messageEl.textContent = text;
    
    // Add to message stream
    messageStream.appendChild(messageEl);
    
    // Scroll to bottom
    messageStream.scrollTop = messageStream.scrollHeight;
}

// Clear all messages from the UI
function clearMessages() {
    const messageStream = document.querySelector('.message-stream');
    messageStream.innerHTML = '';
    window.neonizeUI.appState.messages = [];
}

// Load message history from server
function loadMessageHistory() {
    // Only load if connected
    if (window.neonizeUI.appState.connectionStatus !== 'connected') {
        return;
    }
    
    fetch('/api/messages')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear existing messages
                clearMessages();
                
                // Add messages to UI
                data.messages.forEach(message => {
                    addMessageToUI(message);
                });
                
                // Add system message
                addSystemMessageToUI(`Loaded ${data.messages.length} messages from history`);
            }
        })
        .catch(error => {
            window.neonizeUI.handleError(error, 'loading message history');
        });
}

// Update recipient selector with contacts and groups
function updateRecipientSelector() {
    const recipientSelect = document.getElementById('recipient-select');
    const { contacts, groups } = window.neonizeUI.appState;
    
    // Clear existing options (except placeholder)
    while (recipientSelect.options.length > 1) {
        recipientSelect.remove(1);
    }
    
    // Add contacts
    if (contacts.length > 0) {
        const contactsGroup = document.createElement('optgroup');
        contactsGroup.label = 'Contacts';
        
        contacts.forEach(contact => {
            const option = document.createElement('option');
            option.value = contact.id;
            option.textContent = contact.name || contact.number;
            contactsGroup.appendChild(option);
        });
        
        recipientSelect.appendChild(contactsGroup);
    }
    
    // Add groups
    if (groups.length > 0) {
        const groupsGroup = document.createElement('optgroup');
        groupsGroup.label = 'Groups';
        
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            groupsGroup.appendChild(option);
        });
        
        recipientSelect.appendChild(groupsGroup);
    }
}

// Setup socket event handlers for messages
function setupMessageSocketEvents() {
    // New message received
    socket.on('new_message', (message) => {
        console.log('New message received:', message);
        addMessageToUI(message);
        
        // Play notification sound for incoming messages
        if (!message.is_outgoing) {
            playNotificationSound();
        }
    });
    
    // Contacts updated
    socket.on('contacts_updated', (data) => {
        console.log('Contacts updated:', data);
        window.neonizeUI.appState.contacts = data.contacts;
        updateRecipientSelector();
    });
    
    // Groups updated
    socket.on('groups_updated', (data) => {
        console.log('Groups updated:', data);
        window.neonizeUI.appState.groups = data.groups;
        updateRecipientSelector();
    });
}

// Play notification sound
function playNotificationSound() {
    // Create audio element
    const audio = new Audio();
    audio.src = 'data:audio/mp3;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaWdTb3VuZEJhbmsuY29tIC8gTGFTb25vdGhlcXVlLm9yZwBURU5DAAAAHQAAA1N3aXRjaCBQbHVzIMKpIE5DSCBTb2Z0d2FyZQBUSVQyAAAABgAAAzIyMzUAVFNTRQAAAA8AAANMYXZmNTcuODMuMTAwAAAAAAAAAAAAAAD/80DEAAAAA0gAAAAATEFNRTMuMTAwVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQsRbAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQMSkAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV';
    audio.play();
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Expose functions globally
window.sendMessage = sendMessage;
window.clearMessages = clearMessages;
window.loadMessageHistory = loadMessageHistory;