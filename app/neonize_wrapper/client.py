import os
import base64
from io import BytesIO
from threading import Thread
import time
from flask_socketio import emit
from neonize import WhatsApp
from neonize.models import Message

from .. import socketio

class NeonizeClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NeonizeClient, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.connection_status = "disconnected"
            cls._instance.qr_code_data = None
            cls._instance.message_history = []
            cls._instance.contacts = []
            cls._instance.groups = []
        return cls._instance
    
    def initialize(self, session_path):
        """Initialize the WhatsApp client"""
        if self.client is not None:
            return
            
        try:
            self.client = WhatsApp(session=session_path)
            self.connection_status = "initializing"
            
            # Start connection process in a separate thread
            Thread(target=self._connect).start()
            
        except Exception as e:
            self.connection_status = "error"
            print(f"Error initializing Neonize client: {e}")
    
    def _connect(self):
        """Connect to WhatsApp and handle QR code if needed"""
        try:
            # Custom QR handler to capture QR code for frontend display
            def qr_callback(qr_code):
                # Convert terminal QR to base64 image for web display
                self.qr_code_data = qr_code
                socketio.emit('qr_code', {'qr_data': qr_code})
            
            # Message handler
            def message_handler(message):
                self._process_message(message)
            
            # Set up event handlers
            self.client.on_ready = self._on_ready
            self.client.on_message = message_handler
            self.client.on_qr = qr_callback
            
            # Connect to WhatsApp
            self.client.start()
            
        except Exception as e:
            self.connection_status = "error"
            socketio.emit('connection_status', {'status': 'error', 'message': str(e)})
    
    def _on_ready(self):
        """Handle successful connection"""
        self.connection_status = "connected"
        socketio.emit('connection_status', {'status': 'connected'})
        
        # Fetch contacts and groups after successful connection
        Thread(target=self._load_contacts_and_groups).start()
    
    def _load_contacts_and_groups(self):
        """Load contacts and groups from WhatsApp"""
        try:
            # Fetch contacts
            self.contacts = self.client.get_contacts()
            socketio.emit('contacts_updated', {'contacts': [
                {'id': c.id, 'name': c.name, 'number': c.number} 
                for c in self.contacts
            ]})
            
            # Fetch groups
            self.groups = self.client.get_groups()
            socketio.emit('groups_updated', {'groups': [
                {'id': g.id, 'name': g.name, 'participants': len(g.participants)} 
                for g in self.groups
            ]})
            
        except Exception as e:
            print(f"Error loading contacts and groups: {e}")
    
    def _process_message(self, message):
        """Process incoming messages and emit to frontend"""
        try:
            # Add to message history
            self.message_history.append(message)
            
            # Limit message history size
            if len(self.message_history) > 100:
                self.message_history = self.message_history[-100:]
            
            # Convert message to dictionary for frontend
            message_data = {
                'id': message.id,
                'chat_id': message.chat_id,
                'sender': message.sender.name if message.sender else 'Unknown',
                'sender_id': message.sender.id if message.sender else None,
                'text': message.text,
                'timestamp': message.timestamp.isoformat(),
                'is_group': message.is_group,
                'group_name': message.chat.name if message.is_group else None,
                'type': message.type,
                'is_outgoing': message.is_outgoing
            }
            
            # Emit message to connected clients
            socketio.emit('new_message', message_data)
            
            # Process message with automation rules
            from ..models.automation import AutomationManager
            AutomationManager().process_message(message)
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def send_message(self, recipient_id, message_text):
        """Send a message to a specific recipient"""
        if not self.client or self.connection_status != "connected":
            return False, "Not connected to WhatsApp"
        
        try:
            self.client.send_message(recipient_id, message_text)
            return True, "Message sent successfully"
        except Exception as e:
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from WhatsApp"""
        if self.client:
            try:
                self.client.stop()
                self.connection_status = "disconnected"
                socketio.emit('connection_status', {'status': 'disconnected'})
                return True, "Disconnected successfully"
            except Exception as e:
                return False, str(e)
        return False, "Not connected"