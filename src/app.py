import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from src.api.routes import api, socketio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    # Get the project root directory (parent of src)
    root_dir = Path(__file__).parent.parent
    
    # Load environment variables from config/.env
    env_path = root_dir / 'config' / '.env'
    load_dotenv(env_path)
    
    # Verify environment variables
    required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {missing_vars}")
        
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Initialize SocketIO
    socketio.init_app(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5000)