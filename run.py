import asyncio
import logging
import os
import sys
from app import create_app, socketio

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Get the event loop
    loop = asyncio.get_event_loop()
    
    # Run the Flask app in a separate thread
    def run_flask():
        socketio.run(
            app,
            debug=True,
            host='127.0.0.1',
            port=5000,
            use_reloader=False
        )
    
    # Start Flask in a separate thread
    import threading
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the event loop
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass