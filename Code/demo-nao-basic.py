import json
import time
import os

# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import NAO
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest

# Import Google STT service
from sic_framework.services.google_stt.google_stt import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)

class NaoBasic(SICApplication):
    ### some parts from sic_application: demo_nao_voice_detection.py ###
    def __init__(self):
        super(NaoBasic, self).__init__()

        # input nao ip and api key as a json
        self.nao_ip = "XXX"
        self.google_keyfile_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        # instantiate nao and google_stt
        self.nao = None
        self.google_stt = None

        # configure logging like in demos
        self.set_log_level(sic_logging.INFO)

        self.setup()

    def setup(self):
        self.logger.info("Initializing Nao...")
        self.nao = Nao(ip = self.nao_ip)

        nao_mic = self.nao.mic

        self.logger.info("Loading Google keyfile...")
        with open(self.google_keyfile_path, "r", encoding="utf-8") as f:
            keyfile_json = json.load(f)

        self.logger.info("Setting up Google stt...")
        google_stt_conf = GoogleSpeechToTextConf(
            keyfile_json=keyfile_json,
            sample_rate_hertz=16000, # NAO/Pepper microphone sample rate
            language="en-US",
            timeout=10.0, # listen for max 10 seconds
            interim_results=True,
            model="long", # DOUBLE CHECK MODEL BEFORE RUNNING DEMO
        )

        self.google_stt = GoogleSpeechToText(
            input_source=nao_mic,
            conf=google_stt_conf
        )

        # Optional: receive interim results while the user is still speaking
        self.google_stt.register_callback(self.on_interim_result)

        time.sleep(1)

        self.logger.info("Google STT is ready.")

    def on_interim_result(self, message):
        transcript = self.extract_transcript(message)

        if transcript:
            self.logger.info(f"Transcript: {transcript}")

    def extract_transcript(self, message_or_result):
        """
        Extract transcript text from RecognitionResult.

        RecognitionResult.response may be:
        - a Google StreamingRecognitionResult
        - an empty dict if something failed or timed out
        """

        # If this is a RecognitionResult, get the wrapped response
        response = getattr(message_or_result, "response", message_or_result)

        # Empty response case
        if isinstance(response, dict):
            return None

        # Google result usually has alternatives[0].transcript
        if hasattr(response, "alternatives") and response.alternatives:
            return response.alternatives[0].transcript

        return None

    def listen_once(self):
        """
        Ask the Google STT to transcribe the next thing.
        """

        self.logger.info("Listening...")

        try:
            result = self.google_stt.request(GetStatementRequest())
        except Exception as e:
            self.logger.error(f"Google STT request failed: {e}")
            return None

        transcript = self.extract_transcript(result)

        if transcript:
            self.logger.info(f"Transcript: {transcript}")
            return transcript

        self.logger.info("No Transcript extracted.")
        return None

    def say(self, text):
        """
        Make NAO say something
        """
        self.logger.info("Requesting NAO TTS...")
        try:
            self.nao.tts.request(NaoqiTextToSpeechRequest(str(text)))
        except Exception as e:
            self.logger.error(f"NAO TTS failed: {e}")

        return None

    def run(self):
        """
        Main run loop.
        Repeatedly listens for one user statement and prints the transcript
        """

        self.logger.info("Starting NAO TTS demo...")
        self.logger.info("Press Ctrl+C to stop.")

        self.say("Hello, I am ready to listen.")

        try:
            while not self.shutdown_event.is_set():
                transcript = self.listen_once()

                if transcript:
                    self.logger.info(f"Transcript: {transcript}")
                    # Later LLM logic will be added here
                    self.say("You said"+transcript)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt. Shutting down...")
        except Exception as e:
            self.logger.error(f"NAO TTS demo failed: {e}")
        finally:
            self.shutdown()

if __name__ == "__main__":
    demo = NaoBasic()
    demo.run()