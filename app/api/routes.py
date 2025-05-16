# app/api/routes.py
from flask import Blueprint, jsonify, request, render_template, current_app
import os
import json
from ..neonize_wrapper.client import NeonizeClient
from ..models.automation import AutomationManager, AutomationRule
import uuid

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

# Create blueprint for main routes
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@api_bp.route('/status', methods=['GET'])
def connection_status():
    """Get WhatsApp connection status"""
    client = NeonizeClient()
    return jsonify({
        'status': client.connection_status,
        'qr_code': client.qr_code_data if client.connection_status == 'initializing' else None
    })

@api_bp.route('/connect', methods=['POST'])
def connect():
    """Initialize and connect to WhatsApp"""
    client = NeonizeClient()
    
    # Get session path from config or request
    session_path = request.json.get('session_path', current_app.config['NEONIZE_SESSION_PATH'])
    
    # Initialize client if not already initialized
    if client.connection_status == "disconnected":
        client.initialize(session_path)
        return jsonify({'status': 'initializing', 'message': 'Connecting to WhatsApp...'})
    else:
        return jsonify({'status': client.connection_status, 'message': f'Already in {client.connection_status} state'})

@api_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from WhatsApp"""
    client = NeonizeClient()
    success, message = client.disconnect()
    return jsonify({'success': success, 'message': message})

@api_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    client = NeonizeClient()
    if client.connection_status != "connected":
        return jsonify({'success': False, 'message': 'Not connected to WhatsApp'}), 400
        
    return jsonify({
        'success': True,
        'contacts': [
            {'id': c.id, 'name': c.name, 'number': c.number} 
            for c in client.contacts
        ]
    })

@api_bp.route('/groups', methods=['GET'])
def get_groups():
    """Get all groups"""
    client = NeonizeClient()
    if client.connection_status != "connected":
        return jsonify({'success': False, 'message': 'Not connected to WhatsApp'}), 400
        
    return jsonify({
        'success': True,
        'groups': [
            {'id': g.id, 'name': g.name, 'participants': len(g.participants)} 
            for g in client.groups
        ]
    })

@api_bp.route('/messages', methods=['GET'])
def get_message_history():
    """Get message history"""
    client = NeonizeClient()
    if client.connection_status != "connected":
        return jsonify({'success': False, 'message': 'Not connected to WhatsApp'}), 400
    
    # Convert message objects to dictionaries
    messages = []
    for msg in client.message_history:
        messages.append({
            'id': msg.id,
            'chat_id': msg.chat_id,
            'sender': msg.sender.name if msg.sender else 'Unknown',
            'sender_id': msg.sender.id if msg.sender else None,
            'text': msg.text,
            'timestamp': msg.timestamp.isoformat(),
            'is_group': msg.is_group,
            'group_name': msg.chat.name if msg.is_group else None,
            'type': msg.type,
            'is_outgoing': msg.is_outgoing
        })
    
    return jsonify({
        'success': True,
        'messages': messages
    })

@api_bp.route('/send', methods=['POST'])
def send_message():
    """Send a message to a recipient"""
    client = NeonizeClient()
    
    if client.connection_status != "connected":
        return jsonify({'success': False, 'message': 'Not connected to WhatsApp'}), 400
    
    data = request.json
    recipient_id = data.get('recipient_id')
    message_text = data.get('message')
    
    if not recipient_id or not message_text:
        return jsonify({'success': False, 'message': 'Missing recipient ID or message text'}), 400
    
    success, message = client.send_message(recipient_id, message_text)
    return jsonify({'success': success, 'message': message})

# Automation rule routes
@api_bp.route('/automation/rules', methods=['GET'])
def get_automation_rules():
    """Get all automation rules"""
    automation_manager = AutomationManager()
    rules = [rule.to_dict() for rule in automation_manager.get_rules()]
    return jsonify({'success': True, 'rules': rules})

@api_bp.route('/automation/rules', methods=['POST'])
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

@api_bp.route('/automation/rules/<rule_id>', methods=['PUT'])
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

@api_bp.route('/automation/rules/<rule_id>', methods=['DELETE'])
def delete_automation_rule(rule_id):
    """Delete an automation rule"""
    automation_manager = AutomationManager()
    
    # Delete rule
    success = automation_manager.delete_rule(rule_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Rule not found'}), 404