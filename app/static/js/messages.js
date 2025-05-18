// DOM Elements
const messageStream = document.getElementById('message-stream');
const messageText = document.getElementById('message-text');
const sendBtn = document.getElementById('send-btn');
const contactsList = document.getElementById('contacts-list');
const groupsList = document.getElementById('groups-list');

let selectedChat = null;

// Socket.IO message handling
socket.on('new_message', (message) => {
    addMessageToStream(message);
});

// Add message to the message stream
function addMessageToStream(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_outgoing ? 'message-outgoing' : 'message-incoming'}`;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    if (!message.is_outgoing && message.is_group) {
        const sender = document.createElement('div');
        sender.className = 'message-sender';
        sender.textContent = message.sender;
        content.appendChild(sender);
    }
    
    const text = document.createElement('div');
    text.textContent = message.text;
    content.appendChild(text);
    
    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date(message.timestamp * 1000).toLocaleTimeString();
    content.appendChild(time);
    
    messageDiv.appendChild(content);
    messageStream.appendChild(messageDiv);
    messageStream.scrollTop = messageStream.scrollHeight;
}

// Send message
async function sendMessage() {
    if (!selectedChat || !messageText.value.trim()) return;
    
    try {
        const response = await fetch('/api/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to: selectedChat,
                message: messageText.value.trim()
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        messageText.value = '';
    } catch (error) {
        console.error('Send message error:', error);
        alert('Failed to send message: ' + error.message);
    }
}

// Send button click handler
sendBtn.addEventListener('click', sendMessage);

// Enter key handler for message input
messageText.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Load contacts
async function loadContacts() {
    try {
        const response = await fetch('/api/contacts');
        const data = await response.json();
        
        contactsList.innerHTML = '';
        data.contacts.forEach(contact => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action';
            item.textContent = contact.name || contact.number;
            item.addEventListener('click', () => selectChat(contact.id));
            contactsList.appendChild(item);
        });
    } catch (error) {
        console.error('Load contacts error:', error);
    }
}

// Load groups
async function loadGroups() {
    try {
        const response = await fetch('/api/groups');
        const data = await response.json();
        
        groupsList.innerHTML = '';
        data.groups.forEach(group => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action';
            item.textContent = group.name;
            item.addEventListener('click', () => selectChat(group.id));
            groupsList.appendChild(item);
        });
    } catch (error) {
        console.error('Load groups error:', error);
    }
}

// Select chat
function selectChat(chatId) {
    selectedChat = chatId;
    messageStream.innerHTML = '';
    loadMessages();
}

// Load messages
async function loadMessages() {
    if (!selectedChat) return;
    
    try {
        const response = await fetch('/api/messages');
        const data = await response.json();
        
        if (data.success) {
            messageStream.innerHTML = '';
            data.messages.forEach(message => {
                if (message.chat_id === selectedChat) {
                    addMessageToStream(message);
                }
            });
        }
    } catch (error) {
        console.error('Load messages error:', error);
    }
}

// Load initial data when connected
socket.on('connection_status', (data) => {
    if (data.status === 'connected') {
        loadContacts();
        loadGroups();
    }
}); 