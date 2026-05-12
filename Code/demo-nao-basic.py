import json
import time
import os
import numpy as np

# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import NAO
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest

# Import dialogflow for stt
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)

class NaoBasic(SICApplication):
    ### some parts from sic_application: demo_nao_voice_detection.py ###
    def __init__(self):
        super(NaoBasic, self).__init__()

        self.load_env("../.env")

        # input nao ip and api key as a json
        self.nao_ip = os.environ["NAO_IP"]
        self.google_keyfile_path = os.environ["GOOGLE_KEYFILE_PATH"]

        # instantiate nao and dialogflow
        self.nao = None
        self.dialogflow = None
        self.session_id = np.random.randint(10000)

        # configure logging like in demos
        self.set_log_level(sic_logging.INFO)

        self.setup()

    # on_dialog function (From sic_applications/demo_nao_dialogflow.py
    def on_dialog(self, message):
        """
        Callback function for Dialogflow recognition results.

        Args:
            message: The Dialogflow recognition result message.

        Returns:
            None
        """
        if message.response:
            if message.response.recognition_result.is_final:
                self.logger.info(
                    "Transcript: {}".format(
                        message.response.recognition_result.transcript
                    )
                )

    def setup(self):
        self.logger.info("[setup]: Initializing Nao...")
        self.nao = Nao(ip = self.nao_ip)
        nao_mic = self.nao.mic

        self.logger.info("[setup]: Loading Google keyfile...")
        # Load dialogflow keyfile (From sic_applications/demo_nao_dialogflow.py)
        keyfile_json = json.load(open(self.google_keyfile_path))

        # Set up the config (From sic_applications/demo_nao_dialogflow.py)
        conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000)

        self.logger.info("[setup]: Setting up Dialogflow...")
        # Initiate Dialogflow object (From sic_applications/demo_nao_dialogflow.py)
        self.dialogflow = Dialogflow(ip="localhost", conf=conf, input_source=nao_mic)

        # Register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)

        time.sleep(1)

        self.logger.info("Dialogflow is ready.")

    def extract_transcript(self, reply):
        response = getattr(reply, "response", None)

        if not hasattr(response, "query_result") or response is None:
            return None

        if hasattr(response, "query_result") and response.query_result:
            return response.query_result.query_text

        return None

    def extract_fulfillment_message(self, reply):
        if hasattr(reply, "fulfillment_message") and reply.fulfillment_message:
            self.logger.info("[Nao reply]:" + str(reply.fulfillment_message))
            return reply.fulfillment_message

        return None

    def listen_once(self):
        """
        Get Dialogflow to transcribe the next thing.
        """

        self.logger.info("[listen_once]: Listening...")

        try:
            reply = self.dialogflow.request(GetIntentRequest(self.session_id))
        except Exception as e:
            self.logger.error(f"[listen_once]: Dialogflow request failed: {e}")
            return None, None

        transcript = self.extract_transcript(reply)
        fulfillment_message = self.extract_fulfillment_message(reply)

        if transcript:
            if fulfillment_message:
                self.logger.info("[listen_once]: Returning transcript and fulfillment message.")
                return transcript, fulfillment_message
            self.logger.info(f"[listen_once]: No fulfillment message, returning transcript.")
            return transcript, None

        self.logger.info("[listen_once]: No Transcript or fulfillment message.")
        return None, None

    def say(self, text):
        """
        Make NAO say something
        """
        self.logger.info("[say]: Requesting NAO TTS...")
        try:
            self.nao.tts.request(NaoqiTextToSpeechRequest(str(text)))
        except Exception as e:
            self.logger.error(f"[say]: NAO TTS failed: {e}")

        return None

    def run(self):
        """
        Main run loop.
        Repeatedly listens for one user statement and prints the transcript
        """

        self.logger.info("[run]: Starting NAO TTS demo...")
        self.logger.info("[run]: Press Ctrl+C to stop.")

        self.say("Hello, I am ready to listen.")

        try:
            while not self.shutdown_event.is_set():
                transcript,fulfillment_message = self.listen_once()

                if transcript:
                    self.logger.info(f"[run]: Transcript: {transcript}")
                    # Later LLM logic will be added here
                if fulfillment_message:
                    self.logger.info("[run]: Requesting nao to say fulfillment message.")
                    self.say(fulfillment_message)
        except KeyboardInterrupt:
            self.logger.info("[run]: Keyboard interrupt. Shutting down...")
        except Exception as e:
            self.logger.error(f"[run]: NAO TTS demo failed: {e}")
        finally:
            self.shutdown()

if __name__ == "__main__":
    demo = NaoBasic()
    demo.run()