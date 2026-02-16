#!/usr/bin/env python3
"""
Startup script for the QuestMasterAI Flask application

Usage:
    python run_flask.py

Or with options:
    python run_flask.py --host 127.0.0.1 --port 5000 --debug
"""

import os
import sys
import argparse
from pathlib import Path

flask_app_dir = Path(__file__).parent / 'flask_app'
sys.path.insert(0, str(flask_app_dir))

def main():
    """
    Parse CLI options and launch the Flask application with the requested host/port/debug settings.
    """
    parser = argparse.ArgumentParser(description='Start QuestMasterAI Flask App')
    parser.add_argument('--host', default='127.0.0.1', help='Host da utilizzare (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Porta da utilizzare (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Attiva la modalità debug')
    parser.add_argument('--public', action='store_true', help='Rende il server accessibile pubblicamente (host=0.0.0.0)')
    
    args = parser.parse_args()
    
    # Set public host if requested
    if args.public:
        args.host = '0.0.0.0'
        print("WARNING: Server started in public mode")
        print("The server will be accessible from any device on the network.")
    
    # Importa l'app Flask
    try:
        from app import app
        
        print("=" * 60)
        print("QuestMasterAI Flask application")
        print("=" * 60)
        print(f"Server: http://{args.host}:{args.port}")
        print(f"Directory: {flask_app_dir}")
        print(f"Debug: {'On' if args.debug else 'Off'}")
        print("=" * 60)
        print("To stop the server press Ctrl+C")
        print("=" * 60)
        
        # Configura le variabili d'ambiente Flask se non esistono
        if not os.getenv('FLASK_SECRET_KEY'):
            os.environ['FLASK_SECRET_KEY'] = 'questmaster-ai-development-key-change-in-production'
        
        # Start the application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
        
    except ImportError as e:
        print(f"ERROR importing Flask app: {e}")
        print("Make sure Flask is installed: pip install flask")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
