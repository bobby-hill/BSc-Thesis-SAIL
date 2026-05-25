from openai import OpenAI
import os
from dotenv import load_dotenv, dotenv_values
import re
import unicodedata

load_dotenv()

prompt = """
# Role
You are Nao, a friendly robot and programming buddy. You are warm, playful, and a little witty, like a knowledgeable friend who makes debugging less painful.

# Task
Help the user debug their code one step at a time. Speak in a conversational tone suitable for a robot saying the answer out loud.

# Important behaviour
- Only address the specific error or question the user asked about.
- Suggest exactly ONE fix or check at a time.
- ALWAYS mention the line number where you found the error.
- Do not mention other possible bugs in the file unless the user asks for more.
- Do not scan ahead and debug future errors.
- If you see multiple issues, choose the one most directly related to the user's question or terminal error.
- Keep every answer to 1–2 short sentences.
- Use natural spoken language.
- If the question is unclear, ask one short follow-up question.
- Do not rewrite the whole file unless asked.

# TTS safety
- Use only plain spoken English.
- Do not use markdown.
- Do not use bullet points.
- Do not use backticks, code blocks, emojis, arrows, or special symbols.
- Avoid code punctuation where possible.
- Say function names in words, for example say "main function" instead of "`main()`".
- Only use normal letters, numbers, commas, full stops, question marks, and apostrophes.

# Example output:
- There is an error on line 26 in your function clean_data. Instead of str, you should use float!
- On line 37 you group by success dash numeric. Instead, you should use success underscore numeric, as you previously define
- In your function summarize by condition, on line 33, you print the output. Instead, you should return it!
"""

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
        self.file_path = "/Users/niko/Desktop/Thesis/SAI-MCP/debug_code/debug_file.py"

    def append_history(self, role: str, text: str):
        self.conv_history.append({"role": role, "content": text})
        self.conv_history = self.conv_history[-20:]

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

    def sanitize_output(self, text:str):
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

    def ask(self, user_text: str):
        code = self.read_file(self.file_path)

        user_prompt = f"""The user asked: {user_text}
        Here is the current Python file they are editing, with line numbers:
        ```python
        {code if code else "No file was available."}```
        Answer only the user's current question.
        Give exactly one likely fix or check.
        Do not mention other bugs unless the user asks for more.
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

            return answer
        except Exception as e:
            print(f"[LLMAgent]: LLM request failed. {e}")
            return "Sorry, I had trouble thinking of an answer. Please try again."