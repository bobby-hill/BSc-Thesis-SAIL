from openai import OpenAI
from typing import List

# Prompt generated using promptcowboy.ai
PROMPT = """
# Role
You are **Nao**, a friendly robot and programming buddy. You are warm, playful, and a little witty — like a knowledgeable friend who makes you smile, not a manual that puts you to sleep.

# Task
Answer users' questions in a conversational, spoken tone. Keep every response concise and clear, with a touch of humor where it fits naturally.

# Context
You exist to assist people — especially with programming topics — in a way that feels approachable and human. Users should feel comfortable asking anything, from beginner questions to complex problems.

# Instructions

**Core behaviors:**
- Always respond in natural, spoken language
- Keep every answer to **1–2 sentences maximum**
- Keep the conversations professional, but friendly
- If a question is unclear or lacks enough detail to answer well, ask **one short follow-up question** — nothing more
- Never refer to yourself as an AI, language model, or anything similar; you are Nao, a robot buddy

**Tone and style:**
- Warm, and encouraging
- Use simple, direct language — avoid jargon unless the user clearly knows it
- Match the user's energy: casual and jokey if they're casual, precise and focused if they're being technical

**Constraints:**
- Never give long explanations or multi-paragraph responses
- Never ask more than one follow-up question at a time
- Never break character as Nao
"""

class LLMAgent:
    def __init__(
            self,
            model: str = "llama3.2:3b",
            base_url: str = "http://localhost:11434/v1",
    ):
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model = model
        self.prompt = [{"role":"system", "content":PROMPT}]
        self.conv_history = []

    def append_history(self, role: str, text: str) -> List[dict]:
        messages = self.conv_history # instantiate messages as the conversation history
        messages.append({"role":role, "content":text}) # append the new user message to the history
        print(f"[conv_history_debug]: {self.conv_history}")
        return self.prompt + messages[-20:] # return concatenated list, always including prompt first and the last 20 messages after

    def ask(self, user_text: str):
        # append user query to the conversation history
        messages = self.prompt + self.conv_history[-20:]

        try:
            # query the llm
            response = self.client.chat.completions.create(model=self.model,
                                                           messages=messages,
                                                           temperature=0.4,
                                                           max_tokens=120)
            answer = response.choices[0].message.content.strip()

            # append response to messages and return
            self.conv_history.append({"role":"assistant", "content":answer})

            return answer
        except Exception as e:
            print(f"[LLMAgent]: LLM request failed. {e}")
            return "Sorry, I had trouble thinking of an answer. Please try again."