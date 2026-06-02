import random
from typing import Literal
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nao-gesture-server")

GESTURES = gestures = {
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

@mcp.tool()
def choose_nao_gesture(
    gesture_tag: Literal[
        "no",
        "this",
        "enthusiastic",
        "please",
        "idk",
        "explain",
        "talk",
        "hey",
        "you",
        "thinking",
        "confused",
        "yes",
        "count_one",
        "count_two",
        "count_three",
        "count_four",
        "count_five",
        "count_more",
        "calm_down",
        "reject",
        "give",
        "whatsthis",
        "me",
        "show_sky",
        "show_floor",
        "everything",
        "look",
        "choice",
        "maybe",
        "great",
        "applause",
        "joy",
        "excited",
        "surprised",
        "shy",
        "come_on",
    ],
    reason: str = "",
) -> dict:
    """
    Choose a safe NAO gesture animation path from a small approved gesture bank.
    Use this when Nao should gesture while speaking.
    """
    gesture_path = random.choice(GESTURES[gesture_tag])

    return {
        "gesture_tag": gesture_tag,
        "gesture_path": gesture_path,
        "reason": reason,
    }


if __name__ == "__main__":
    mcp.run()