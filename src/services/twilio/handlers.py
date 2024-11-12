import os
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from src.api.arize import process_call

logger = logging.getLogger(__name__)

class TwilioHandler:
    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            logger.error("Twilio credentials not found in environment variables")
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
            
        self.client = Client(account_sid, auth_token)

    def handle_incoming_call(self):
        """Handle incoming phone calls"""
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            action="/process_speech",
            timeout=3,
            speech_timeout="auto"
        )
        gather.say("Nine-one-one what is your emergency.")
        response.append(gather)
        response.redirect("/answer")
        return str(response)

    def handle_speech_processing(self, speech_result: str, socketio):
        """Process the speech input from the caller"""
        if speech_result:
            result = process_call(speech_result)
            logger.info(f"Processing result: {result}")

            response = VoiceResponse()
            response.say(f"I heard: {speech_result}")
            socketio.emit("send_message", result)
            response.say(f"Processing result: {result}")
        else:
            logger.warning("No speech detected")
            response = VoiceResponse()
            response.say("I'm sorry, I didn't catch that. Please try again.")
            response.redirect("/answer")

        return str(response)