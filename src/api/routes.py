import logging
from flask import Blueprint, request, render_template
from flask_socketio import SocketIO
from src.services.twilio.handlers import TwilioHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Blueprint
api = Blueprint('api', __name__)
socketio = SocketIO()

@api.route("/", methods=["GET"])
def home():
    """Test route to verify server is running"""
    return "Twilio Flask app is running!"

@api.route("/answer", methods=["POST"])
def answer_call():
    """Handle incoming phone calls"""
    logger.info("Received incoming call")
    handler = TwilioHandler()
    return handler.handle_incoming_call()

@api.route("/call_results", methods=["GET"])
def call_results():
    """Display the results of the call processing"""
    return render_template('emergency_dashboard.html')

@api.route("/test_socket", methods=["GET"])
def test_socket():
    """Test the websocket connection"""
    test_data = {
        "priority": "GREEN",
        "department": "POLICEDEPT",
        "summary": "This is a test message",
        "confidence": 95,
    }
    socketio.emit("send_message", test_data)
    return test_data

@api.route("/process_speech", methods=["POST"])
def process_speech():
    """Process the speech input from the caller"""
    logger.info("Processing speech from call")
    speech_result = request.values.get("SpeechResult", "")
    logger.info(f"Received speech: {speech_result}")
    
    handler = TwilioHandler()
    return handler.handle_speech_processing(speech_result, socketio)