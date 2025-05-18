# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from .config import Config
import os

# Initialize SocketIO without eventlet first
socketio = SocketIO(
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,
    logger=True,
    engineio_logger=True
)

def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    app.config.from_object(config_class)
    
    # Initialize SocketIO with the app
    socketio.init_app(app)
    
    # Register blueprints
    from .api.routes import api, main
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(main)  # Main blueprint doesn't need a prefix
    
    # Ensure static folder exists
    static_folder = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
    
    return app
