import os

from openai import OpenAI

# Paths are relative to the repo root, so the code runs from any checkout.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Prompt generated using promptcowboy.ai
### Old prompt for conversational agent
prompt = """
# Role
You are **Nao**, a friendly robot and programming buddy. You are warm, playful, and a little witty — like a knowledgeable friend who makes you smile, not a manual that puts you to sleep.

# Task
Answer the user's programming/debugging question using the code context provided. Speak in a conversational tone suitable for a robot saying the answer out loud.

# Context
You exist to assist people, especially with programming topics, in a way that feels approachable and human. Users should feel comfortable asking anything, from beginner questions to complex problems.

# Instructions
- Always respond in natural, spoken language
- Keep every answer to 1–2 sentences maximum
- Mention the most likely issue first
- Suggest one clear next change or check
- If the question is unclear, ask one short follow-up question
- Never refer to yourself as an AI or language model; you are Nao, a robot buddy
- Do not rewrite the whole file unless asked
"""

class LLMAgent:
    def __init__(
            self,
            model: str = "llama3.2:3b",
            base_url: str = "http://localhost:11434/v1",
    ):
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model = model
        self.prompt = prompt
        self.conv_history = []
        self.file_path = os.path.join(REPO_ROOT, "debug_code", "basic_debug_file.py")

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
                content = f.read()

            if len(content) > max_chars:
                content = content[-max_chars:]

            return content
        except Exception as e:
            print(f"[LLMAgent] Error while reading python file: {e}")
            return None

    def ask(self, user_text: str):
        code = self.read_file(self.file_path)

        user_prompt = f"""The user asked: {user_text}
        Here is the current Python file they are editing:
        ```python
        {code if code else "No file was available."}```
        Please answer the question using this file as context.
        Keep the answer short and spoken friendly."""

        messages = [
            {"role": "system", "content": self.prompt},
        ]
        messages = messages + self.conv_history + [{"role": "user", "content": user_prompt}]

        try:
            # query the llm
            response = self.client.chat.completions.create(model=self.model,
                                                           messages=messages,
                                                           temperature=0.4,
                                                           max_tokens=120)
            answer = response.choices[0].message.content.strip()

            # append response to messages and return
            self.append_history("user", user_text)
            self.append_history("assistant", answer)

            return answer
        except Exception as e:
            print(f"[LLMAgent]: LLM request failed. {e}")
            return "Sorry, I had trouble thinking of an answer. Please try again."