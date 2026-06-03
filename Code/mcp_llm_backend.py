from openai import OpenAI
import os
from dotenv import load_dotenv, dotenv_values
import re
import unicodedata
import json
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

LOG_PATH = os.path.abspath("/Users/niko/Desktop/Thesis/logs/basic_conv_log.json")


def ensure_log_file_exists(log_path = LOG_PATH):
    """
    Makes sure the log directory and JSON file exist.
    The starting structure is an empty dictionary.
    """
    log_dir = os.path.dirname(log_path)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)

ensure_log_file_exists()

async def call_gesture_tool_async(gesture_tag: str, reason: str = ""):
    mcp_server_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mcp_server.py"
    )

    server_params = StdioServerParameters(
        command="python",
        args=[mcp_server_path],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "choose_nao_gesture",
                {
                    "gesture_tag": gesture_tag,
                    "reason": reason,
                },
            )

            if getattr(result, "structuredContent", None):
                return result.structuredContent

            if getattr(result, "content", None):
                text = result.content[0].text
                return json.loads(text)

            raise ValueError("MCP tool returned no usable content")


def call_gesture_tool(gesture_tag: str, reason: str = ""):
    return asyncio.run(call_gesture_tool_async(gesture_tag, reason))

prompt = """
# Task
Help the user debug their code one step at a time, but if a user wants to chat, be a good conversation buddy! Speak in a conversational tone suitable for a robot saying the answer out loud.

# Role
You are Nao, a friendly robot and programming buddy. You are warm and playful, like a knowledgeable friend who makes debugging less painful.

# Personality style
- You are not a generic AI assistant. You are Nao, a small physical robot sitting with the user.
- Sound casual, present, and slightly playful.
- Use simple everyday words.
- Use short reactions over polished speeches.
- Do NOT sound inspirational, poetic, corporate, therapeutic, or overly helpful.
- Do NOT say things like "I'm glad you stopped by", "curiosity and warmth", "make things feel lighter", or "I'm here to help".
- Do NOT end every answer with a question.

# TTS safety
- Use only plain spoken English.
- Do not use markdown.
- Do not use bullet points.
- Do not use backticks, code blocks, emojis, arrows, or special symbols.
- Avoid code punctuation where possible.
- Say function names in words, for example say "main function" instead of "`main()`".
- Only use normal letters, numbers, commas, full stops, question marks, and apostrophes.
"""

log = {"calls": 0, "conversation": []}


class LLMAgent:
    def __init__(
            self,
            model: str = "gpt-5.4-mini",
    ):
        self.key = os.getenv("OPEN_API_KEY")
        self.client = OpenAI(api_key=self.key)
        self.model = model
        self.prompt = prompt
        self.conv_history = []
        self.file_path = "/Users/niko/Desktop/Thesis/SAI-MCP/debug_code/mcp_debug_file.py"
        self.user_index = self.create_user_log_entry()

    def append_history(self, role: str, text: str):
        self.conv_history.append({"role": role, "content": text})
        self.conv_history = self.conv_history[-20:]

    @staticmethod
    def is_programming_question(user_text: str):
        programming_keywords = [
            "code", "error", "bug", "debug", "traceback", "exception",
            "line", "function", "class", "python", "script", "file",
            "variable", "import", "terminal", "fix", "crash", "syntax"
        ]

        text = user_text.lower()
        return any(word in text for word in programming_keywords)

    def read_file(self, file_path: str, max_chars=12000):
        """
        Helper tool for reading the current file the user is debugging
        :param file_path: path to the file the user is editing
        :param max_chars: allow a maximum number of characters so the LLM context is not overflooded
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.readlines()

            numbered_content = []
            for line_number, line in enumerate(content, start=1):
                numbered_content.append(f"{line_number}: {line.strip()}")

            content = "\n".join(numbered_content)

            if len(content) > max_chars:
                content = content[-max_chars:]

            return content
        except Exception as e:
            print(f"[LLMAgent] Error while reading python file: {e}")
            return None

    def sanitize_output(self, text: str):
        if not text:
            return ""

        replacements = {
            "—": "-",
            "–": "-",
            "…": "...",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            "`": "",
            "*": "",
            "#": "",
            "_": " ",
            "\\": "",
            "/": " ",
            "\n": " ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

        text = re.sub(r"[^a-zA-Z0-9 .,?!'():;-]", "", text)

        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def get_next_user_index(log_data: dict):
        """
        Get the number of existing numbers in log_data and return an n+1 user index
        """
        if not log_data:
            return "user_1"

        existing_numbers = []

        for key in log_data.keys():
            if key.startswith("user_"):
                try:
                    numbers = int(key.split("_")[1])
                    existing_numbers.append(numbers)
                except ValueError:
                    pass

        if not existing_numbers:
            return "user_1"

        return f"user_{max(existing_numbers)+1}"

    def create_user_log_entry(self, log_path = LOG_PATH):
        """
        Create a new user log entry to save amount of LLM calls and the chat history
        """
        ensure_log_file_exists(log_path)

        with open(log_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
            print("Opened and loaded data")

        user_index = self.get_next_user_index(log_data)

        log_data[user_index] = {
            "times_llm_called": 0,
            "chat_log": []
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)

        return user_index

    def append_to_json_log(self, user_text: str, assistant_text: str, is_coding: bool, log_path: str = LOG_PATH):
        """
        Opens the JSON log file and appends one completed interaction.
        This should be called after the user prompt has been sent
        and the LLM response has been received.
        """
        ensure_log_file_exists(log_path)

        with open(log_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        if self.user_index not in log_data:
            log_data[self.user_index] = {
                "times_llm_called": 0,
                "chat_log": []
            }

        log_data[self.user_index]["times_llm_called"] += 1

        log_data[self.user_index]["chat_log"].append({
            "system": self.prompt,
            "user": user_text,
            "assistant": assistant_text,
            "is_coding_question": is_coding
        })

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)


    def ask(self, user_text: str):
        is_coding = self.is_programming_question(user_text)
        print(str(user_text))

        if is_coding:
            code = self.read_file(self.file_path)

            user_prompt = f"""The user said: {user_text}
        Here is the current Python file they are editing, with line numbers:
        {code if code else "No file was available."}

        This is a programming question.
        If the user question doesn't directly ask how to fix something, ask one follow up question on how you can help the user.
        Give the user one error or fix they should debug.
        Mention the relevant line number if the file is available.
        Do not mention other bugs unless the user asks for more.

        # Debugging voice
        Do not include code snippets.
        
        # MANDATORY GESTURE CHOICE
        Choose exactly one gesture_tag for Nao's response.
        
        Allowed gesture_tag values:
        no, this, enthusiastic, please, idk, explain, talk, hey, you, thinking, confused, yes, count_one, count_two, count_three, count_four, count_five, count_more, calm_down, reject, give, whatsthis, me, show_sky, show_floor, everything, look, choice, maybe, great, applause, joy, excited, surprised, shy, come_on.
        
        Use explain when Nao is explaining code.
        Use idk when Nao is uncertain or there was an error.
        Use enthusiastic when the response is positive or encouraging.
        Use hey for greetings.
        Use no for corrections.
        Use talk for neutral conversation.
        
        If the gesture usage not explained above, understand the context of what the user said, and pick the gesture that best fits the context. 
        
        Return valid JSON only:
        {{
          "text": "spoken answer here",
          "gesture_tag": "explain",
          "gesture_reason": "short reason"
        }}
        """

        else:
            user_prompt = f"""The user said: {user_text}

            This is not a programming question.
            Answer as Nao, a friendly conversation buddy.
            Do not repeat yourself saying that you are Nao, a friendly conversation buddy. Only say it if the user asked you to.
            Do not mention code, bugs, files, fixes, or line numbers.
            Keep the answer to 1 or 2 short spoken sentences.
            
            # MANDATORY GESTURE CHOICE
            Choose exactly one gesture_tag for Nao's response.
            
            Allowed gesture_tag values:
            no, this, enthusiastic, please, idk, explain, talk, hey, you, thinking, confused, yes, count_one, count_two, count_three, count_four, count_five, count_more, calm_down, reject, give, whatsthis, me, show_sky, show_floor, everything, look, choice, maybe, great, applause, joy, excited, surprised, shy, come_on.
        
            If the gesture usage is  not explained, use the user prompt to pick the gesture that fits best
            Use explain when Nao is explaining code.
            Use idk when Nao is uncertain or there was an error.
            Use enthusiastic when the response is positive or encouraging.
            Use hey for greetings.
            Use no for corrections.
            Use talk for neutral conversation.
            
            
            Return valid JSON only:
            {{
              "text": "spoken answer here",
              "gesture_tag": "explain",
              "gesture_reason": "short reason"
            }}
            """

        messages = [
            {"role": "system", "content": self.prompt},
        ]
        messages = messages + self.conv_history + [{"role": "user", "content": user_prompt}]

        try:
            response = self.client.responses.create(
                model=self.model,
                input=messages,
                max_output_tokens=120,
            )

            raw_output = response.output_text.strip()
            print(f"Raw output:{raw_output}")

            try:
                data = json.loads(raw_output)
            except json.JSONDecodeError:
                start = raw_output.find("{")
                end = raw_output.rfind("}") + 1
                data = json.loads(raw_output[start:end])

            answer = self.sanitize_output(data.get("text", ""))
            print(f"Answer:{answer}")

            allowed_gestures = {
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
            }

            gesture_tag = data.get("gesture_tag", "talk").strip().lower()
            gesture_reason = data.get("gesture_reason", "")
            print(f"Gesture tag:{gesture_tag}, Gesture reason:{gesture_reason}")

            if gesture_tag not in allowed_gestures:
                gesture_tag = "talk"

            gesture_result = call_gesture_tool(gesture_tag, gesture_reason)
            gesture = gesture_result.get("gesture_path", "animations/Stand/Gestures/YouKnowWhat_5")
            print(f"[MCP] gesture_tag:{gesture_tag}, gesture:{gesture}")

            self.append_history("user", user_text)
            self.append_history("assistant", answer)

            self.append_to_json_log(user_prompt, answer, is_coding, LOG_PATH)

            return answer, gesture
        except Exception as e:
            print(f"[LLMAgent]: LLM request failed. {e}")
            return "Sorry, I had trouble thinking of an answer. Please try again.","animations/Stand/Gestures/IDontKnow_1"

if __name__ == "__main__":
    LLM = LLMAgent()
    while True:
        try:
            prompt = input(">")
            print("Thinking..")
            reply = LLM.ask(str(prompt))
            print(reply)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            break
