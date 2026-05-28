import random
from typing import Literal
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nao-gesture-server")

GESTURES = gestures = {"yes":["animations/Stand/Gestures/Yes_1", "animations/Stand/Gestures/Yes_3"],
                    "no":["animations/Stand/Gestures/No_3", "animations/Stand/Gestures/No_8","animations/Stand/Gestures/No_9"],
                    "idk":["animations/Stand/Gestures/IDontKnow_1","animations/Stand/Gestures/IDontKnow_2"],
                    "please":["animations/Stand/Gestures/Please_1"],
                    "explain":["animations/Stand/Gestures/Explain_1","animations/Stand/Gestures/Explain_2","animations/Stand/Gestures/Explain_3","animations/Stand/Gestures/Explain_4","animations/Stand/Gestures/Explain_5"],
                    "enthusiastic":["animations/Stand/Gestures/Enthusiastic_4","animations/Stand/Gestures/Enthusiastic_5"],
                    "talk":["animations/Stand/Gestures/YouKnowWhat_1","animations/Stand/Gestures/YouKnowWhat_5"],
                    "hey":["animations/Stand/Gestures/Hey_1","animations/Stand/Gestures/Hey_6"],
                    "you":["animations/Stand/Gestures/You_1", "animations/Stand/Gestures/You_4"]
                    }

@mcp.tool()
def choose_nao_gesture(
    gesture_tag: Literal[
        "yes",
        "no",
        "idk",
        "please",
        "explain",
        "enthusiastic",
        "talk",
        "hey",
        "you",
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