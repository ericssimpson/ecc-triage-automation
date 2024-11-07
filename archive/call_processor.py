from dotenv import load_dotenv
from openai import OpenAI
import speech_recognition as sr
import json
import os
import logging

from enum import Enum
from typing import Optional, Dict, Any, List
import sqlite3
from dataclasses import dataclass

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class EmergencyPriority(Enum):
    GREEN = 3
    ORANGE = 2
    RED = 1


class Department(Enum):
    EMS = 3
    FIREDEPT = 2
    POLICEDEPT = 1


@dataclass
class EmergencyCall:
    transcript: str
    priority: Optional[EmergencyPriority] = None
    department: Optional[Department] = None
    summary: Optional[str] = None
    confidence: Optional[int] = None
    raw_audio: Optional[Any] = None


class AudioTranscriptionError(Exception):
    """Custom exception for audio transcription failures."""

    pass


class EmergencyCallProcessor:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.recognizer = sr.Recognizer()

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def record_audio(self) -> Optional[str]:
        """
        Record audio from microphone and transcribe it to text.

        Returns:
            str: Transcribed text if successful, None otherwise
        """
        try:
            with sr.Microphone() as source:
                logger.info("Please speak now...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
                logger.info("Recording finished, processing...")

            text = self.recognizer.recognize_google(audio)
            logger.info(f"Transcription successful: {text}")
            return text

        except sr.UnknownValueError:
            logger.error("Could not understand the audio")
            raise AudioTranscriptionError("Failed to understand the audio")
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            raise AudioTranscriptionError(f"Speech recognition service failed: {e}")

    def analyze_emergency(self, call: EmergencyCall) -> EmergencyCall:
        """
        Analyze the emergency call transcript using OpenAI to determine priority and extract key information.

        Args:
            call: EmergencyCall object containing the transcript

        Returns:
            EmergencyCall: Updated with priority and analysis
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """
                    You are an operator for a emergency call line, you simply need to determine, rapidly, if the text you see qualifies as 1 of three possible options. 

                    you will provide will be in the form of a JSON, such as (priority: 'RED' ) (summary: 'car suspicious hoodie' ) (department: 'POLICEDEPT') ( confidence: '80' ) 

                    1: RED - the words you are hearing qualify as needing rapid emergency services, and the operator will need to read text that says "This is an emergency CODE RED" - for example, if the person is bleeding, saying words like "please help" "coming after me" "knife" "gun" - things of that nature, that raise an immediate alarm.

                    2: ORANGE - the words you are hearing qualify as in the middle, where a sense of urgency is involved, but might not qualify as needing an ambulance deployed to the location immediately. This might happen if the person is saying "umm" or "wait" or if you are unsure if it's an immediate emergency, or if it could be something non-serious.

                    3: GREEN - the nature of the call doesn't sound immediately dangerous, as in, the person calling is reporting a missing cat, or issuing a noise complaint about their neighbor, which doesn't require any type of immediate response. Example might be, the person is calling about a suspicious person, or car in their neighborhood.

                    Also, you will only provide the threat level in terms of its priority - followed by a three word summary - or the words used by the caller that indicate to you that there is indeed a justification for the chosen priority. And you will rate your confidence in the priority level you have assigned things to.

                    In addition, you will provide the department this call will be dispatched to.
                    
                    1: EMS - the words you are hearing relate to people or living animals' physical health, such as bleeding out , injury, and coma. 
                    
                    2: FIRDEPT - the words you are hearing relate to the fire hazard in public space and require fire department to operate.  
                    
                    3: POLICEDEPT - the words you are hearing relate to the violence, community safety, and everything concerning policing. 

                    An example output you will provide will be in the form of a JSON, such as 
                    (priority: 'GREEN' ) (summary: 'cat tree lost' ) (department: 'POLICEDEPT') ( confidence: '60' )
                    
                    Respond in JSON format with these fields:
                    {
                        "priority": "PRIORITY_LEVEL",
                        "summary": "summary of event"
                        "department": "DEPARTMENT"
                    }
                    """,
                    },
                    {"role": "user", "content": call.transcript},
                ],
            )

            analysis = json.loads(response.choices[0].message.content)
            call.priority = EmergencyPriority[analysis["priority"]]
            call.department = Department[analysis["department"]]
            call.analysis = analysis

            logger.info(f"Emergency analyzed - Priority: {call.priority.name}")
            return call

        except Exception as e:
            logger.error(f"Error analyzing emergency: {e}")
            raise
