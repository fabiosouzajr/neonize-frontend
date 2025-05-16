import re
import json
import os
from datetime import datetime

class AutomationRule:
    def __init__(self, rule_id, name, trigger_type, trigger_pattern, actions, is_active=True):
        self.id = rule_id
        self.name = name
        self.trigger_type = trigger_type  # 'message_text', 'sender', 'group', etc.
        self.trigger_pattern = trigger_pattern  # Regex pattern or exact match
        self.actions = actions  # List of actions to perform
        self.is_active = is_active
    
    def matches(self, message):
        """Check if the message matches this rule's trigger conditions"""
        if not self.is_active:
            return False
            
        if self.trigger_type == 'message_text':
            # Match against message text using regex
            return re.search(self.trigger_pattern, message.text, re.IGNORECASE) is not None
            
        elif self.trigger_type == 'sender':
            # Match against sender ID or name
            if message.sender:
                return (message.sender.id == self.trigger_pattern or 
                        message.sender.name == self.trigger_pattern)
            return False
            
        elif self.trigger_type == 'group':
            # Match against group ID or name
            if message.is_group and message.chat:
                return (message.chat.id == self.trigger_pattern or 
                        message.chat.name == self.trigger_pattern)
            return False
            
        return False
    
    def to_dict(self):
        """Convert rule to dictionary for storage/transmission"""
        return {
            'id': self.id,
            'name': self.name,
            'trigger_type': self.trigger_type,
            'trigger_pattern': self.trigger_pattern,
            'actions': self.actions,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create rule from dictionary"""
        return cls(
            rule_id=data.get('id'),
            name=data.get('name'),
            trigger_type=data.get('trigger_type'),
            trigger_pattern=data.get('trigger_pattern'),
            actions=data.get('actions'),
            is_active=data.get('is_active', True)
        )


class AutomationManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomationManager, cls).__new__(cls)
            cls._instance.rules = []
            cls._instance._load_rules()
        return cls._instance
    
    def _load_rules(self):
        """Load automation rules from storage"""
        try:
            rules_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'automation_rules.json')
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(rules_file), exist_ok=True)
            
            if os.path.exists(rules_file):
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                    self.rules = [AutomationRule.from_dict(rule) for rule in rules_data]
            else:
                # Create sample rules if no rules exist
                self._create_sample_rules()
                self._save_rules()
                
        except Exception as e:
            print(f"Error loading automation rules: {e}")
            self._create_sample_rules()
    
    def _create_sample_rules(self):
        """Create sample automation rules"""
        self.rules = [
            AutomationRule(
                rule_id="1",
                name="Auto-Reply to Hello",
                trigger_type="message_text",
                trigger_pattern="^(hello|hi|hey)$",
                actions=[{
                    "type": "reply",
                    "text": "Hello! This is an automated response from Neonize."
                }]
            ),
            AutomationRule(
                rule_id="2",
                name="Forward Important Messages",
                trigger_type="message_text",
                trigger_pattern="\\b(urgent|important)\\b",
                actions=[{
                    "type": "forward",
                    "destination": "admin_contact_id"  # Replace with actual contact ID
                }]
            )
        ]
    
    def _save_rules(self):
        """Save automation rules to storage"""
        try:
            rules_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'automation_rules.json')
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(rules_file), exist_ok=True)
            
            with open(rules_file, 'w') as f:
                json.dump([rule.to_dict() for rule in self.rules], f, indent=2)
                
        except Exception as e:
            print(f"Error saving automation rules: {e}")
    
    def add_rule(self, rule):
        """Add a new automation rule"""
        self.rules.append(rule)
        self._save_rules()
        return rule.id
    
    def update_rule(self, rule_id, updated_rule):
        """Update an existing automation rule"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules[i] = updated_rule
                self._save_rules()
                return True
        return False
    
    def delete_rule(self, rule_id):
        """Delete an automation rule"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                self._save_rules()
                return True
        return False
    
    def get_rules(self):
        """Get all automation rules"""
        return self.rules
    
    def process_message(self, message):
        """Process a message against all automation rules"""
        from ..neonize_wrapper.client import NeonizeClient
        
        client = NeonizeClient()
        
        for rule in self.rules:
            if rule.matches(message):
                for action in rule.actions:
                    self._execute_action(action, message, client)
    
    def _execute_action(self, action, message, client):
        """Execute a single automation action"""
        action_type = action.get('type')
        
        if action_type == 'reply':
            # Reply to the message
            text = action.get('text', '')
            client.send_message(message.chat_id, text)
            
        elif action_type == 'forward':
            # Forward the message to another chat
            destination = action.get('destination')
            if destination:
                forward_text = f"Forwarded message from {message.sender.name if message.sender else 'Unknown'}: {message.text}"
                client.send_message(destination, forward_text)
                
        elif action_type == 'log':
            # Log the message to a file
            log_file = action.get('file', 'message_log.txt')
            log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_path = os.path.join(log_dir, log_file)
            with open(log_path, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sender = message.sender.name if message.sender else 'Unknown'
                f.write(f"[{timestamp}] {sender}: {message.text}\n")