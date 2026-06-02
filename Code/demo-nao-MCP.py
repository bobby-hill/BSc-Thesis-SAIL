import json
import time
import os
import random

import numpy as np

# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import NAO
from sic_framework.devices import Nao # Nao base class
from sic_framework.devices.nao import NaoqiTextToSpeechRequest # Nao TTS service
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoRestRequest,
    NaoSetAutonomousLifeRequest,
    NaoBasicAwarenessRequest,
    NaoBackgroundMovingRequest,
    NaoListeningMovementRequest,
    NaoSpeakingMovementRequest,
) # Import nao life autonomous processes
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

from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoLEDRequest, # Nao led request to reset leds after some animations
    NaoFadeRGBRequest # Nao RGB leds request
)

# Import dialogflow for stt
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)

# Import local LLM
from mcp_llm_backend import LLMAgent

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
                        self.stop_facetracking()
                        time.sleep(0.2)
                        self.stop_breathing()
                        time.sleep(0.2)
                        self.nao.autonomous.request(NaoRestRequest())
                        time.sleep(0.2)
                        self.shutdown()

    def pick_gesture(self, tag:str):
        """
        Randomly pick a gesture from Nao's gesture bank
        Available gesture tags: yes, no, idk, please, explain, enthusiastic, talk, hey, you
        """
        gestures = {
            "no": [
                "animations/Stand/Gestures/No_5",
                "animations/Stand/Gestures/No_4",
                "animations/Stand/Gestures/No_9",
                "animations/Stand/Gestures/No_1",
                "animations/Stand/Gestures/No_7"
            ],
            "this": [
                "animations/Stand/Gestures/This_13",
                "animations/Stand/Gestures/This_8",
                "animations/Stand/Gestures/This_3",
                "animations/Stand/Gestures/This_7",
                "animations/Stand/Gestures/This_14"
            ],
            "enthusiastic": [
                "animations/Stand/Gestures/Enthusiastic_1",
                "animations/Stand/Gestures/Enthusiastic_5",
                "animations/Stand/Gestures/Enthusiastic_4",
                "animations/Stand/Gestures/Enthusiastic_2",
                "animations/Stand/Gestures/Enthusiastic_3"
            ],
            "please": [
                "animations/Stand/Gestures/Please_3",
                "animations/Stand/Gestures/Please_2",
                "animations/Stand/Gestures/Please_1"
            ],
            "idk": [
                "animations/Stand/Gestures/IDontKnow_3",
                "animations/Stand/Gestures/IDontKnow_2",
                "animations/Stand/Gestures/IDontKnow_1",
                "animations/Stand/Gestures/IDontKnow_5",
                "animations/Stand/Gestures/IDontKnow_4"
            ],
            "explain": [
                "animations/Stand/Gestures/Explain_1",
                "animations/Stand/Gestures/Explain_5",
                "animations/Stand/Gestures/Explain_11",
                "animations/Stand/Gestures/Explain_2",
                "animations/Stand/Gestures/Explain_6"
            ],
            "talk": [
                "animations/Stand/Gestures/YouKnowWhat_5",
                "animations/Stand/Gestures/YouKnowWhat_3",
                "animations/Stand/Gestures/YouKnowWhat_2",
                "animations/Stand/Gestures/YouKnowWhat_4",
                "animations/Stand/Gestures/YouKnowWhat_1"
            ],
            "hey": [
                "animations/Stand/Gestures/Hey_3",
                "animations/Stand/Gestures/Hey_7",
                "animations/Stand/Gestures/Hey_1",
                "animations/Stand/Gestures/Hey_6",
                "animations/Stand/Gestures/Hey_4"
            ],
            "you": [
                "animations/Stand/Gestures/You_3",
                "animations/Stand/Gestures/You_1",
                "animations/Stand/Gestures/You_4",
                "animations/Stand/Gestures/You_5",
                "animations/Stand/Gestures/You_2"
            ],
            "thinking": [
                "animations/Stand/Gestures/Thinking_7",
                "animations/Stand/Gestures/Thinking_4",
                "animations/Stand/Gestures/Thinking_1",
                "animations/Stand/Gestures/Thinking_2",
                "animations/Stand/Gestures/Thinking_5"
            ],
            "confused": [
                "animations/Stand/Gestures/Confused_1",
                "animations/Stand/Gestures/Confused_2"
            ],
            "yes": [
                "animations/Stand/Gestures/Yes_2",
                "animations/Stand/Gestures/Yes_1",
                "animations/Stand/Gestures/Yes_3"
            ],
            "count_one": [
                "animations/Stand/Gestures/CountOne_2",
                "animations/Stand/Gestures/CountOne_1"
            ],
            "count_two": [
                "animations/Stand/Gestures/CountTwo_2",
                "animations/Stand/Gestures/CountTwo_1"
            ],
            "count_three": [
                "animations/Stand/Gestures/CountThree_1",
                "animations/Stand/Gestures/CountThree_2"
            ],
            "count_four": [
                "animations/Stand/Gestures/CountFour_2",
                "animations/Stand/Gestures/CountFour_1"
            ],
            "count_five": [
                "animations/Stand/Gestures/CountFive_1",
                "animations/Stand/Gestures/CountFive_2"
            ],
            "count_more": [
                "animations/Stand/Gestures/CountMore_2",
                "animations/Stand/Gestures/CountMore_1"
            ],
            "calm_down": [
                "animations/Stand/Gestures/CalmDown_5",
                "animations/Stand/Gestures/CalmDown_2",
                "animations/Stand/Gestures/CalmDown_1",
                "animations/Stand/Gestures/CalmDown_3",
                "animations/Stand/Gestures/CalmDown_6"
            ],
            "reject": [
                "animations/Stand/Gestures/Reject_2",
                "animations/Stand/Gestures/Reject_4",
                "animations/Stand/Gestures/Reject_1",
                "animations/Stand/Gestures/Reject_5",
                "animations/Stand/Gestures/Reject_6"
            ],
            "give": [
                "animations/Stand/Gestures/Give_6",
                "animations/Stand/Gestures/Give_5",
                "animations/Stand/Gestures/Give_3",
                "animations/Stand/Gestures/Give_4",
                "animations/Stand/Gestures/Give_2"
            ],
            "whatsthis": [
                "animations/Stand/Gestures/WhatSThis_4",
                "animations/Stand/Gestures/WhatSThis_12",
                "animations/Stand/Gestures/WhatSThis_9",
                "animations/Stand/Gestures/WhatSThis_6",
                "animations/Stand/Gestures/WhatSThis_1"
            ],
            "me": [
                "animations/Stand/Gestures/Me_2",
                "animations/Stand/Gestures/Me_3",
                "animations/Stand/Gestures/Me_4",
                "animations/Stand/Gestures/Me_6",
                "animations/Stand/Gestures/Me_5"
            ],
            "show_sky": [
                "animations/Stand/Gestures/ShowSky_7",
                "animations/Stand/Gestures/ShowSky_6",
                "animations/Stand/Gestures/ShowSky_3",
                "animations/Stand/Gestures/ShowSky_10",
                "animations/Stand/Gestures/ShowSky_11"
            ],
            "show_floor": [
                "animations/Stand/Gestures/ShowFloor_2",
                "animations/Stand/Gestures/ShowFloor_4",
                "animations/Stand/Gestures/ShowFloor_3",
                "animations/Stand/Gestures/ShowFloor_5",
                "animations/Stand/Gestures/ShowFloor_1"
            ],
            "everything": [
                "animations/Stand/Gestures/Everything_4",
                "animations/Stand/Gestures/Everything_2",
                "animations/Stand/Gestures/Everything_1",
                "animations/Stand/Gestures/Everything_5",
                "animations/Stand/Gestures/Everything_3"
            ],
            "look": [
                "animations/Stand/Gestures/Look_2",
                "animations/Stand/Gestures/Look_1"
            ],
            "choice": [
                "animations/Stand/Gestures/Choice_2",
                "animations/Stand/Gestures/Choice_1"
            ],
            "maybe": [
                "animations/Stand/Gestures/Maybe_1"
            ],
            "great": [
                "animations/Stand/Gestures/Great_1"
            ],
            "applause": [
                "animations/Stand/Gestures/Applause_1"
            ],
            "joy": [
                "animations/Stand/Gestures/Joy_1"
            ],
            "excited": [
                "animations/Stand/Gestures/Excited_1"
            ],
            "surprised": [
                "animations/Stand/Gestures/Surprised_1"
            ],
            "shy": [
                "animations/Stand/Gestures/Shy_1"
            ],
            "come_on": [
                "animations/Stand/Gestures/ComeOn_1"
            ],
        }

        try:
            gesture = random.choice(gestures[str(tag)])
            return gesture
        except Exception as e:
            self.logger.info(f"[pick_gesture]: {e}")
            return None


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

        self.nao.leds.request(NaoLEDRequest("FaceLeds", True))

        # Get nao to stand
        try:
            self.nao.motion.request(NaoPostureRequest(target_posture="Stand", speed=0.5))
            time.sleep(3)
        except Exception as e:
            print(e)
            return None

        # Start autonomous functions
        self.nao.autonomous.request(NaoBasicAwarenessRequest(True))
        self.nao.autonomous.request(NaoBackgroundMovingRequest(True))
        time.sleep(0.2)

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
            self.nao.stiffness.request(Stiffness(stiffness=0.5, joints=["Head"]))
            self.nao.tracker.request(
                StartTrackRequest(
                    target_name="Face", size=0.2, mode="Head", effector="None"
                )
            )
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

    # functions to start and stop face tracking and breathing in one function
    def start_live(self):
        try:
            self.start_facetracking()
            self.start_breathing()
        except Exception as e:
            self.logger.info(f"Error starting breathing and facetracking: {e}")

    def stop_live(self):
        try:
            self.stop_breathing()
            self.stop_facetracking() # For now dont stop face tracking while doing gestures
        except Exception as e:
            self.logger.info(f"Error stopping breathing and facetracking: {e}")


    def say(self, text, blocking=True,animated=False, gesture=None):
        """
        Make NAO say something. By default: blocking=False animated=False
        :blocking: Whether the tts request will block other requests to the robot
        :animated: Whether a filler animation will be used while Nao speaks
        :gesture: Optional gesture path if we want the robot to do a gesture while speaking
        """
        text = f"\\vol=50\\ \\rspd=93\\ {text}"
        try:
            if animated == False and blocking == False and gesture: # Get nao to perform a gesture while speaking
                self.logger.info("[say] Requesting Nao to say with gesture..")

                self.nao.motion.request(NaoqiAnimationRequest(str(gesture)), block=False) # Perform gesture while speaking
                self.nao.tts.request(NaoqiTextToSpeechRequest(str(text), animated=False), block=True)

                self.nao.leds.request(NaoLEDRequest("FaceLeds", True)) # Reset leds after some animations
            elif animated: # Get nao to perform some movements while speaking
                self.logger.info("[say] Requesting Nao to say with animated..")
                self.nao.tts.request(NaoqiTextToSpeechRequest(str(text), animated=True), block=True)
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

        # Get llm to generate a hello response + warmup llm
        greeting = self.llm_agent.ask("Hello there!")
        if greeting:
            text, gesture = greeting
            self.say(text=text, animated=False, blocking=False, gesture=gesture)
        else: # If no llm response, use fallback
            self.say(text="""Hello there!
                          "My name is Nao, and I am your coding buddy for today.
                          "Feel free to ask me anything about programming, or, if you have an error that's bugging you,
                          we can fix it together! Just ask me when you need me.""", blocking=False, gesture=self.pick_gesture("yes"))

        try:
            while not self.shutdown_event.is_set():
                self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", r=0, g=1, b=0, duration=0)) # Turn leds to green while listening
                transcript,fulfillment_message, intent, action = self.listen_once()

                if transcript: # if dialogflow successfully transcribed the speech
                    self.nao.leds.request(NaoLEDRequest("FaceLeds", True)) # Turn leds back to white

                    self.logger.info(f"[run]: Transcript: {transcript}") # log the transcription

                    if self.df_reply(intent, action) and fulfillment_message: # if there's a known intent or action, we can use smalltalk from dialogflow
                        self.logger.info("[run]: Intent identified, using fulfillment message.")

                        self.say(text=fulfillment_message, animated=False, gesture=self.pick_gesture("enthusiastic"), blocking=False)

                    else: # if no intent, we need to call llm for the response
                        self.logger.info(f"[run]: Sending transcript to LLM Agent...")
                        self.say(text="mmm...", blocking=False, animated=False, gesture=self.pick_gesture("explain"))
                        response = self.llm_agent.ask(transcript) # try to get response from llm

                        if response: # if there's a response
                            text, gesture = response
                            self.logger.info(f"[run]: LLM Response: {response}; LLM Gesture: {gesture}") # log response
                            self.say(text=text,animated=False, blocking=False, gesture=gesture) # get nao to say it

                        elif fulfillment_message: # if there's no response, try fulfillment message
                            self.logger.info("[run]: Requesting nao to say fulfillment message.")
                            self.say(text=fulfillment_message,animated=False, blocking=False, gesture=self.pick_gesture("talk")) # get nao to say fulfillment message

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