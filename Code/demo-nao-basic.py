import json
import time
import os
import numpy as np

# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import NAO
from sic_framework.devices import Nao # Nao base class
from sic_framework.devices.nao import NaoqiTextToSpeechRequest # Nao TTS service
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest # Nao rest position
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
    NaoqiBreathingRequest,
) # Nao motion service

from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness # Nao face tracking stuff
from sic_framework.devices.common_naoqi.naoqi_tracker import (
    RemoveTargetRequest,
    StartTrackRequest,
    StopAllTrackRequest,
) # Nao face tracking stuff

# Import dialogflow for stt
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)

# Import local LLM
from llm_backend import LLMAgent

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

        # instantiate llm agent
        self.llm_agent = LLMAgent(model="gpt-5.4-mini")

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

    def on_button_press(self, button_message):
        self.logger.info(f"Nao Button Pressed: {button_message.value}")

        for i in button_message.value:
            if 'Head' in i:
                for j in i:
                    if j == 1:
                        self.logger.info("Requesting rest position.")
                        self.say("Im sleepy", animated=False,blocking=True)
                        time.sleep(5)
                        self.nao.autonomous.request(NaoRestRequest())
                        self.shutdown()

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

        # Register a callback function when Naos button is pressed
        self.nao.buttons.register_callback(self.on_button_press)

        time.sleep(1)

        self.logger.info("Dialogflow is ready.")

    def listen_once(self):
        """
        Get Dialogflow to transcribe the next thing.
        Big gate block to check if all the return values were received.
        """

        self.logger.info("[listen_once]: Listening...")

        try:
            reply = self.dialogflow.request(GetIntentRequest(self.session_id))
            if hasattr(reply, "response"):
                if hasattr(reply.response, "query_result"):
                    reply = reply.response.query_result
                    self.logger.info(f"[DEBUG]: {reply}")
        except Exception as e:
            self.logger.error(f"[listen_once]: Dialogflow request failed: {e}")
            return None, None, None, None

        transcript = getattr(reply, "query_text", None)
        fulfillment_message = getattr(reply, "fulfillment_text", None)
        action = getattr(reply, "action", None)
        if hasattr(reply, "intent"):
            if hasattr(reply.intent, "display_name"):
                intent = reply.intent.display_name
        else:
            intent = None

        # use if else gates to check for each component.
        # intent and action can be available independently depending on context
        # so we need to check for both, either, or none
        if transcript:
            if fulfillment_message:
                if intent and action:
                    self.logger.info("[listen_once]: Returning all df returns")
                    return transcript, fulfillment_message, str(intent), str(action)
                elif intent or action:
                    if intent:
                        self.logger.info("[listen_once]: Returning everything except action")
                        return transcript, fulfillment_message, str(intent), None
                    self.logger.info("[listen_once]: Returning everything except intent")
                    return transcript, fulfillment_message, None, str(action)
                else:
                    self.logger.info(f"[listen_once]: No intent or action, returning transcript and fulfillment message.")
                    return transcript, fulfillment_message, None, None
            else:
                self.logger.info(f"[listen_once]: No intent and fulfillment message, returning transcript")
                return transcript, None, None, None
        self.logger.info("[listen_once]: No Transcript, Fulfillment message, or Intent.")
        return None, None, None, None

    # Start Nao face tracking
    def start_facetracking(self):
        self.logger.info("Starting face tracking..")
        try:
            self.nao.stiffness.request(Stiffness(stiffness=0.6, joints=["Head"]))
            self.nao.tracker.request(
                StartTrackRequest(
                    target_name="Face", size=0.2, mode="Head", effector="None"
                )
            )
            time.sleep(1)
        except Exception as e:
            self.logger.info(f"Face tracking failed: {e}")

    # Stop Nao face tracking
    def stop_facetracking(self):
        self.logger.info("Stopping face tracking..")
        try:
            self.nao.tracker.request(RemoveTargetRequest(target_name="Face"))
            time.sleep(0.2)
            self.nao.stiffness.request(Stiffness(stiffness=0.15, joints=["Head"]))
        except Exception as e:
            self.logger.info(f"Error stopping face tracking: {e}")

    def start_breathing(self):
        try:
            self.logger.info("Starting breathing..")
            self.nao.motion.request(NaoqiBreathingRequest(joints="Arms", value=True)) # Switched Body to Arms
        except Exception as e:
            self.logger.info(f"Error starting breathing: {e}")

    def stop_breathing(self):
        try:
            self.logger.info("Stopping breathing..")
            self.nao.motion.request(NaoqiBreathingRequest(joints="Arms", value=False))
        except Exception as e:
            self.logger.info(f'Error stopping breathing: {e}')

    def say(self, text, blocking=True,animated=False, gesture=None):
        """
        Make NAO say something. By default: blocking=False animated=False
        :blocking: Whether the tts request will block other requests to the robot
        :animated: Whether a filler animation will be used while Nao speaks
        :gesture: Optional gesture path if we want the robot to do a gesture while speaking
        """
        text = f"\\vol=80\\ \\rspd=80\\ {text}"
        try:
            if animated == False and blocking == False and gesture: # Get nao to perform a gesture while speaking
                self.stop_facetracking() # Stop face tracking to prevent interference with gestures
                self.stop_breathing()
                time.sleep(0.2)

                self.logger.info("[say] Requesting Nao to say with gesture..")
                self.nao.tts.request(NaoqiTextToSpeechRequest(str(text), animated=False), block=False)

                self.nao.motion.request(NaoqiAnimationRequest(str(gesture)), block=True) # Perform gesture while speaking

                self.start_facetracking() # Resume face tracking
                self.start_breathing()
            elif animated: # Get nao to perform some movements while speaking
                self.stop_facetracking()
                self.stop_breathing()
                time.sleep(0.2)

                self.logger.info("[say] Requesting Nao to say with animated..")
                self.nao.tts.request(NaoqiTextToSpeechRequest(str(text), animated=True), block=True)

                self.start_facetracking()
                self.start_breathing()
            else:
                # Do not turn off face tracking or breathing for simple tts requests
                self.logger.info("[say] Requesting Nao to say normally..")
                self.nao.tts.request(NaoqiTextToSpeechRequest(str(text), animated=animated), block=blocking)
        except Exception as e:
            self.logger.error(f"[say]: NAO TTS failed: {e}")

        return None

    # identify if intent is known
    def df_reply(self,intent: str, action: str):
        """
        Dialog Flow intent/action check.
        Check if the intent or action returned for the user utterance is known.
        Used to decide in run() whether to use the fulfillment message or not.
        """
        intents = ["Help Intent", "Default Welcome Intent"]

        if action and action.startswith("smalltalk"):
            return True
        elif intent in intents:
            return True
        return False

    def run(self):
        """
        Main run loop.
        Repeatedly listens for one user statement and prints the transcript
        """
        self.logger.info("[run]: Starting NAO TTS demo...")
        self.logger.info("[run]: Press Ctrl+C to stop.")

        self.start_facetracking()

        self.logger.info("[run] Requesting stand position.")
        self.nao.motion.request(NaoPostureRequest(target_posture="Stand", speed=0.5))
        time.sleep(1)

        # Greeting + initialisation
        self.say(text="""Hello there!
                      "My name is Nao, and I am your coding buddy for today.
                      "Feel free to ask me anything about programming, or, if you have an error that's bugging you,
                      we can fix it together! Just ask me when you need me.""", blocking=False, gesture="animations/Stand/Gestures/Hey_6")
        time.sleep(8)

        try:
            while not self.shutdown_event.is_set():
                transcript,fulfillment_message, intent, action = self.listen_once()

                if transcript: # if dialogflow successfully transcribed the speech
                    self.logger.info(f"[run]: Transcript: {transcript}") # log the transcription

                    if self.df_reply(intent, action) and fulfillment_message: # if there's a known intent or action, we can use smalltalk from dialogflow
                        self.logger.info("[run]: Intent identified, using fulfillment message.")
                        self.say(text=fulfillment_message, animated=True)

                    else: # if no intent, we need to call llm for the response
                        self.logger.info(f"[run]: Sending transcript to LLM Agent...")
                        self.say(text="Let me think..", blocking=False, animated=True)
                        response = self.llm_agent.ask(transcript) # try to get response from llm

                        if response: # if there's a response
                            self.logger.info(f"[run]: LLM Response: {response}") # log response
                            self.logger.info(f"[run]: Requesting nao to say LLM response")
                            self.say(text=response,animated=True) # get nao to say it

                        elif fulfillment_message: # if there's no response, try fulfillment message
                            self.logger.info("[run]: Requesting nao to say fulfillment message.")
                            self.say(text=fulfillment_message,animated=True) # get nao to say fulfillment message

                        else: # if nothing works use fallback
                            self.logger.info("[run]: No LLM response or Fulfillment message. Using fallback...")
                            self.say(text="I had trouble coming up with a response...", gesture="animations/Stand/Gestures/IDontKnow_1")
        except KeyboardInterrupt:
            self.logger.info("[run]: Keyboard interrupt. Shutting down...")
        except Exception as e:
            self.logger.error(f"[run]: NAO TTS demo failed: {e}")
        finally:
            self.shutdown()

if __name__ == "__main__":
    demo = NaoBasic()
    demo.run()