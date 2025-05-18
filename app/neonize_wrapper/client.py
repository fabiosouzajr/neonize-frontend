import os
import base64
from io import BytesIO
import asyncio
from threading import Thread
import time
from flask_socketio import emit
from neonize.aioze.client import NewAClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    FutureProofMessage,
    InteractiveMessage,
    MessageContextInfo,
    DeviceListMetadata,
)
from neonize.types import MessageServerID
from neonize.utils import log
from neonize.utils.enum import ReceiptType
import qrcode
import io
from icecream import ic
import re
import logging
import eventlet

from .. import socketio

class WhatsAppClient:
    def __init__(self, session_path):
        """Initialize the WhatsApp client"""
        self.session_path = os.path.abspath(session_path)
        self.client = None
        self.connected = False
        self.qr_code_data = None
        self.message_history = []
        self.contacts = []
        self.groups = []
        self.loop = None
        
        # Create session directory if it doesn't exist
        os.makedirs(self.session_path, exist_ok=True)
        
    def connect(self):
        """Connect to WhatsApp"""
        try:
            ic("Starting connection process")
            # Create new client instance with SQLite database
            db_path = os.path.join(self.session_path, "db.sqlite3")
            self.client = NewAClient(db_path)
            ic("Client instance created")
            
            # Set up event handlers
            @self.client.event(ConnectedEv)
            async def on_connected(_: NewAClient, __: ConnectedEv):
                try:
                    ic("Connected event received")
                    self.connected = True
                    socketio.emit('connection_status', {'status': 'connected'})
                    # Load contacts and groups after connection
                    await self._load_contacts_and_groups()
                    ic("Contacts and groups loaded")
                except Exception as e:
                    ic(f"Error in connected handler: {str(e)}")
                    socketio.emit('error', {'message': f'Connection Error: {str(e)}'})
            
            @self.client.event(MessageEv)
            async def on_message(_: NewAClient, message: MessageEv):
                try:
                    ic(f"Message received: {message.Info.ID}")
                    self._process_message(message)
                except Exception as e:
                    ic(f"Error in message handler: {str(e)}")
                    socketio.emit('error', {'message': f'Message Error: {str(e)}'})
            
            @self.client.event(PairStatusEv)
            async def on_pair_status(_: NewAClient, message: PairStatusEv):
                try:
                    ic(f"Pair status received: {message.ID.User}")
                    socketio.emit('connection_status', {'status': 'paired'})
                except Exception as e:
                    ic(f"Error in pair status handler: {str(e)}")
                    socketio.emit('error', {'message': f'Pair Status Error: {str(e)}'})
            
            # Set QR callback
            def on_qr(qr_data: str):
                try:
                    ic(f"QR code received: {qr_data}")
                    # Generate QR code with specific settings
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    
                    # Create image with specific settings
                    qr_img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Convert to base64
                    buffered = BytesIO()
                    qr_img.save(buffered, format="PNG")
                    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Emit QR code to frontend
                    socketio.emit('qr_code', {'qr': qr_base64})
                    ic("QR code emitted to frontend")
                    
                except Exception as e:
                    ic(f"Error in QR handler: {str(e)}")
                    socketio.emit('error', {'message': f'QR Error: {str(e)}'})
            
            self.client.on_qr = on_qr
            ic("QR callback set")
            
            # Start connection
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.client.connect())
            ic("Connection completed")
            
        except Exception as e:
            ic(f"Error in connect method: {str(e)}")
            socketio.emit('error', {'message': f'Connection Error: {str(e)}'})
            raise e
    
    def _connect(self):
        """Connect to WhatsApp in background thread"""
        try:
            ic("Starting background connection")
            
            # Set connection status to connecting
            socketio.emit('connection_status', {'status': 'connecting'})
            
            # Run the connection with eventlet
            def run_async():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.client.connect())
                except Exception as e:
                    ic(f"Error in async connection: {str(e)}")
                    socketio.emit('error', {'message': f'Connection Error: {str(e)}'})
                    self.connected = False
                    socketio.emit('connection_status', {'status': 'disconnected'})
            
            # Run in a separate thread to avoid blocking
            eventlet.spawn(run_async)
            ic("Background connection started")
        except Exception as e:
            ic(f"Error in _connect method: {str(e)}")
            socketio.emit('error', {'message': f'Connection Error: {str(e)}'})
            self.connected = False
            socketio.emit('connection_status', {'status': 'disconnected'})
    
    async def _load_contacts_and_groups(self):
        """Load contacts and groups from WhatsApp"""
        try:
            ic("Loading contacts and groups")
            # Get all contacts
            contacts = await self.client.contact.get_all_contacts()
            self.contacts = [
                {'id': c.id, 'name': c.name, 'number': c.number} 
                for c in contacts
            ]
            socketio.emit('contacts_updated', {'contacts': self.contacts})
            ic(f"Contacts loaded: {len(self.contacts)}")
            
            # Get all groups
            groups = await self.client.get_joined_groups()
            self.groups = [
                {'id': g.JID.id, 'name': g.GroupName.Name, 'participants': len(g.Participants)} 
                for g in groups
            ]
            socketio.emit('groups_updated', {'groups': self.groups})
            ic(f"Groups loaded: {len(self.groups)}")
            
        except Exception as e:
            ic(f"Error loading contacts and groups: {str(e)}")
            socketio.emit('error', {'message': str(e)})
    
    def _process_message(self, message):
        """Process incoming messages and emit to frontend"""
        try:
            ic(f"Processing message: {message.Info.ID}")
            # Add to message history
            self.message_history.append(message)
            
            # Limit message history size
            if len(self.message_history) > 100:
                self.message_history = self.message_history[-100:]
            
            # Convert message to dictionary for frontend
            message_data = {
                'id': message.Info.ID,
                'chat_id': message.Info.MessageSource.Chat.id,
                'sender': message.Info.MessageSource.Sender.name if message.Info.MessageSource.Sender else 'Unknown',
                'sender_id': message.Info.MessageSource.Sender.id if message.Info.MessageSource.Sender else None,
                'text': message.Message.conversation if message.Message.conversation else '',
                'timestamp': message.Info.Timestamp,
                'is_group': message.Info.MessageSource.IsGroup,
                'group_name': message.Info.MessageSource.Chat.name if message.Info.MessageSource.IsGroup else None,
                'type': message.Info.Type,
                'is_outgoing': message.Info.MessageSource.IsFromMe
            }
            
            # Emit message to connected clients
            socketio.emit('new_message', message_data)
            ic(f"Message processed and emitted: {message.Info.ID}")
            
        except Exception as e:
            ic(f"Error processing message: {str(e)}")
            socketio.emit('error', {'message': str(e)})
    
    async def send_message_async(self, recipient_id, message_text):
        """Send a message to a specific recipient using async"""
        if not self.client or not self.connected:
            return False, "Not connected to WhatsApp"
        
        try:
            # Create JID for recipient
            from neonize.utils.jid import build_jid
            recipient_jid = build_jid(recipient_id, "s.whatsapp.net")
            
            # Send message
            response = await self.client.send_message(recipient_jid, message_text)
            
            # Emit sent message to frontend
            socketio.emit('new_message', {
                'to': recipient_id,
                'content': message_text,
                'type': 'sent',
                'id': response.ID
            })
            
            return True, "Message sent successfully"
        except Exception as e:
            socketio.emit('error', {'message': str(e)})
            return False, str(e)
    
    def send_message(self, recipient_id, message_text):
        """Synchronous wrapper for sending messages"""
        try:
            if not self.loop:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            success, message = self.loop.run_until_complete(self.send_message_async(recipient_id, message_text))
            return success, message
        except Exception as e:
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from WhatsApp"""
        if self.client:
            try:
                if not self.loop:
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(self.client.disconnect())
                self.connected = False
                socketio.emit('connection_status', {'status': 'disconnected'})
                return True, "Disconnected successfully"
            except Exception as e:
                return False, str(e)
        return False, "Not connected"
    
    def get_contacts(self):
        """Get all contacts"""
        return self.contacts
    
    def get_groups(self):
        """Get all groups"""
        return self.groups