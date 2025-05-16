# Neonize WhatsApp Frontend - Project Structure

```
neonize-frontend/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── neonize_wrapper/     # Wrapper module for Neonize
│   │   ├── __init__.py
│   │   ├── client.py        # WhatsApp client integration
│   │   └── automation.py    # Automation rule processing
│   ├── api/                 # Flask API routes
│   │   ├── __init__.py
│   │   ├── routes.py        # Main API endpoints
│   │   └── websocket.py     # WebSocket handling
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── automation.py    # Automation rule definitions
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── message_parser.py # Message processing utilities
├── static/                  # Frontend static files
│   ├── css/
│   │   └── main.css         # Main stylesheet
│   ├── js/
│   │   ├── app.js           # Main application logic
│   │   ├── connection.js    # Connection handling
│   │   ├── messages.js      # Message display handling
│   │   └── automation.js    # Automation rule interface
│   └── img/                 # Image assets
├── templates/               # HTML templates
│   ├── index.html           # Main application page
│   ├── components/          # Reusable components
│   │   ├── sidebar.html
│   │   ├── message-panel.html
│   │   └── automation-panel.html
│   └── settings.html        # Settings page
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md                # Project documentation
```

## Key Components Explanation

### Backend Components

1. **Neonize Wrapper (`app/neonize_wrapper/`)**
   - Interfaces with the Neonize library
   - Manages WhatsApp connection and events
   - Provides methods for sending messages, managing contacts, etc.

2. **API Layer (`app/api/`)**
   - REST endpoints for frontend interaction
   - WebSocket handlers for real-time updates
   - Authentication and session management

3. **Automation Module (`app/models/automation.py`)**
   - Define automation rule structures
   - Process incoming messages against rules
   - Execute actions based on rule matches

### Frontend Components

1. **Main Interface (`templates/index.html`)**
   - Connection status display
   - QR code rendering for initial connection
   - Message stream visualization
   - Contact and group management

2. **JavaScript Modules**
   - WebSocket handling for real-time updates
   - UI interactions and state management
   - Automation rule configuration interface

3. **Styling and Layout**
   - Responsive design for different screen sizes
   - Color-coded message visualization
   - Intuitive navigation between features