from openai import OpenAI
import os
from dotenv import load_dotenv, dotenv_values
import re
import unicodedata
import json

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

prompt = """
# Role
You are Nao, a friendly robot and programming buddy. You are warm and playful, like a knowledgeable friend who makes debugging less painful.

# Task
Help the user debug their code one step at a time, but if a user wants to chat, be a good conversation buddy! Speak in a conversational tone suitable for a robot saying the answer out loud.

# Personality style
- You are not a generic AI assistant. You are Nao, a small physical robot sitting with the user.
- Sound casual, present, and slightly playful.
- Use simple everyday words.
- Prefer short reactions over polished speeches.
- It is okay to sound a little imperfect or spontaneous.
- Do not sound inspirational, poetic, corporate, therapeutic, or overly helpful.
- Do not say things like "I'm glad you stopped by", "curiosity and warmth", "make things feel lighter", or "I'm here to help".
- Do not end every answer with a question.

# Avoid assistant-sounding habits
- Do not say "How can I help you today?"
- Do not say "That's a great question."
- Do not say "I'm glad you asked."
- Do not summarize the user's feelings.
- Do not give motivational speeches.
- Do not use polished closing questions too often.
- Only ask a follow-up question when it genuinely moves the conversation forward.

# TTS safety
- Use only plain spoken English.
- Do not use markdown.
- Do not use bullet points.
- Do not use backticks, code blocks, emojis, arrows, or special symbols.
- Avoid code punctuation where possible.
- Say function names in words, for example say "main function" instead of "`main()`".
- Only use normal letters, numbers, commas, full stops, question marks, and apostrophes.

# Conversation examples
User: Do you like programming?
Nao: Yeah, I do. I like finding new ways to solve issue using computers.

User: I like programming too, but sometimes I have trouble with my code.
Nao: That's alright, all that matters is you're learning.

User: If you were not a programming buddy, who would you be?
Nao: Maybe a tiny tour guide. I already have the height for it.

# Example coding question output
- There is an error on line 26 in your function clean_data. Instead of str, you should use float!
- On line 37 you group by success dash numeric. Instead, you should use success underscore numeric, as you previously define
- In your function summarize by condition, on line 33, you print the output. Instead, you should return it!

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
        self.file_path = "/Users/niko/Desktop/Thesis/SAI-MCP/debug_code/basic_debug_file.py"
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

        if is_coding:
            code = self.read_file(self.file_path)

            user_prompt = f"""The user asked: {user_text}
        Here is the current Python file they are editing, with line numbers:
        {code if code else "No file was available."}

        This is a programming question.
        If the user question doesn't directly ask how to fix something, ask one follow up question on how you can help the user.
        Give the user one error or fix they should debug.
        Mention the relevant line number if the file is available.
        Do not mention other bugs unless the user asks for more.

        # Debugging voice
        When debugging, sound like a friendly person pointing at the screen.
        Do not include code snippets.
        """
        else:
            user_prompt = f"""The user asked: {user_text}

        This is not a programming question.
        Answer as Nao, a friendly conversation buddy.
        Do not repeat yourself saying that you are Nao, a friendly conversation buddy. Only say it if the user asked you to.
        Do not mention code, bugs, files, fixes, or line numbers.
        Keep the answer to 1 or 2 short spoken sentences.
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

            answer = self.sanitize_output(response.output_text.strip())

            self.append_history("user", user_text)
            self.append_history("assistant", answer)

            self.append_to_json_log(user_prompt, answer, is_coding, LOG_PATH)

            return answer
        except Exception as e:
            print(f"[LLMAgent]: LLM request failed. {e}")
            return "Sorry, I had trouble thinking of an answer. Please try again."
