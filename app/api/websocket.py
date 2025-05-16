from flask import request
from flask_socketio import emit
from .. import socketio
from ..neonize_wrapper.client import NeonizeClient

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections"""
    client = NeonizeClient()
    emit('connection_status', {'status': client.connection_status})
    
    # If there's a QR code available and client is initializing, send it
    if client.connection_status == 'initializing' and client.qr_code_data:
        emit('qr_code', {'qr_data': client.qr_code_data})

@socketio.on('request_qr')
def handle_request_qr():
    """Handle request for QR code refresh"""
    client = NeonizeClient()
    if client.connection_status == 'initializing' and client.qr_code_data:
        emit('qr_code', {'qr_data': client.qr_code_data})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    # We don't disconnect from WhatsApp when a WebSocket client disconnects
    # as there could be multiple frontend clients connected
    pass