# app/api/routes.py
from flask import Blueprint, jsonify, request, render_template, current_app
import os
import json
from ..neonize_wrapper.client import WhatsAppClient
from ..models.automation import AutomationManager, AutomationRule
import uuid
from app import socketio
from app.config import Config

# Create blueprint for API routes
api = Blueprint('api', __name__)

# Create blueprint for main routes
main = Blueprint('main', __name__)

whatsapp_client = WhatsAppClient(Config.NEONIZE_SESSION_DIR)

@main.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@api.route('/status', methods=['GET'])
def get_status():
    """Get connection status"""
    return jsonify({
        'status': 'connected' if whatsapp_client.connected else 'disconnected'
    })

@api.route('/connect', methods=['POST'])
def connect():
    """Connect to WhatsApp"""
    try:
        whatsapp_client.connect()
        return jsonify({'status': 'connecting'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from WhatsApp"""
    success, message = whatsapp_client.disconnect()
    if success:
        return jsonify({'status': 'disconnected'})
    return jsonify({'error': message}), 500

@api.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    return jsonify({'contacts': whatsapp_client.get_contacts()})

@api.route('/groups', methods=['GET'])
def get_groups():
    """Get all groups"""
    return jsonify({'groups': whatsapp_client.get_groups()})

@api.route('/messages', methods=['GET'])
def get_message_history():
    """Get message history"""
    if not whatsapp_client.connected:
        return jsonify({'success': False, 'message': 'Not connected to WhatsApp'}), 400
    
    # Convert message objects to dictionaries
    messages = []
    for msg in whatsapp_client.message_history:
        messages.append({
            'id': msg.Info.ID,
            'chat_id': msg.Info.MessageSource.Chat.id,
            'sender': msg.Info.MessageSource.Sender.name if msg.Info.MessageSource.Sender else 'Unknown',
            'sender_id': msg.Info.MessageSource.Sender.id if msg.Info.MessageSource.Sender else None,
            'text': msg.Message.conversation if msg.Message.conversation else '',
            'timestamp': msg.Info.Timestamp,
            'is_group': msg.Info.MessageSource.IsGroup,
            'group_name': msg.Info.MessageSource.Chat.name if msg.Info.MessageSource.IsGroup else None,
            'type': msg.Info.Type,
            'is_outgoing': msg.Info.MessageSource.IsFromMe
        })
    
    return jsonify({
        'success': True,
        'messages': messages
    })

@api.route('/send', methods=['POST'])
async def send_message():
    """Send a message"""
    data = request.get_json()
    if not data or 'to' not in data or 'message' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    success, message = await whatsapp_client.send_message_async(data['to'], data['message'])
    if success:
        return jsonify({'status': 'sent'})
    return jsonify({'error': message}), 500

# Automation rule routes
@api.route('/automation/rules', methods=['GET'])
def get_automation_rules():
    """Get all automation rules"""
    automation_manager = AutomationManager()
    rules = [rule.to_dict() for rule in automation_manager.get_rules()]
    return jsonify({'success': True, 'rules': rules})

@api.route('/automation/rules', methods=['POST'])
def add_automation_rule():
    """Add a new automation rule"""
    automation_manager = AutomationManager()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Missing rule data'}), 400
    
    # Generate a unique ID for the new rule
    rule_id = str(uuid.uuid4())
    
    # Create rule from request data
    rule = AutomationRule(
        rule_id=rule_id,
        name=data.get('name', 'New Rule'),
        trigger_type=data.get('trigger_type'),
        trigger_pattern=data.get('trigger_pattern'),
        actions=data.get('actions', []),
        is_active=data.get('is_active', True)
    )
    
    # Add rule to manager
    automation_manager.add_rule(rule)
    
    return jsonify({'success': True, 'rule_id': rule_id})

@api.route('/automation/rules/<rule_id>', methods=['PUT'])
def update_automation_rule(rule_id):
    """Update an existing automation rule"""
    automation_manager = AutomationManager()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Missing rule data'}), 400
    
    # Create updated rule from request data
    updated_rule = AutomationRule(
        rule_id=rule_id,
        name=data.get('name'),
        trigger_type=data.get('trigger_type'),
        trigger_pattern=data.get('trigger_pattern'),
        actions=data.get('actions', []),
        is_active=data.get('is_active', True)
    )
    
    # Update rule
    success = automation_manager.update_rule(rule_id, updated_rule)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Rule not found'}), 404

@api.route('/automation/rules/<rule_id>', methods=['DELETE'])
def delete_automation_rule(rule_id):
    """Delete an automation rule"""
    automation_manager = AutomationManager()
    
    # Delete rule
    success = automation_manager.delete_rule(rule_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Rule not found'}), 404