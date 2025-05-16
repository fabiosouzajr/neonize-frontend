
# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load config based on config_name
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register the main route
    from .api.routes import main
    app.register_blueprint(main)
    
    return app
