from dotenv import load_dotenv
from openai import OpenAI
import speech_recognition as sr
import os
from arize import process_call

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# def stream_in_audio():


# Function to capture audio and transcribe it
def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Please speak now...")
        audio = recognizer.listen(source)
        print("Recording finished, processing...")

    # Try to transcribe the speech
    try:
        # text = recognizer.recognize_google(audio)

        text = recognizer.recognize_whisper_api(audio, api_key=OPENAI_API_KEY)
        print("Transcription: " + text)
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from the speech recognition service; {e}")
        return None


def generic_text_fn(text):
    # TODO: perform the 911 evaluation here
    outval = process_call(text)
    print(outval)


def main():
    # Record and transcribe audio
    transcribed_text = record_audio()
    if transcribed_text:
        generic_text_fn(transcribed_text)


if __name__ == "__main__":
    main()
