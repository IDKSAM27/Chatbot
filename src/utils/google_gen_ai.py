import json
import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai.client import Chats
from google.genai.types import Content, GenerateContentConfig, Part
from pydantic import BaseModel

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_KEY")


class ChatResponse(BaseModel):
    response: Optional[str] = None


class GoogleAPIHandler:
    def __init__(self):

        self.gemini_api_key = GEMINI_API_KEY
        self.client = genai.Client(api_key=self.gemini_api_key)
        self.prompt = ""

    def refresh_prompt(self):
        with open("src/utils/prompt.txt") as file:
            self.prompt = file.read()

    def chat(self, message: str, chat: Optional[Chats] = None) -> Optional[ChatResponse]:
        if chat is None:
            chat = self.client.chats.create(model="gemini-2.0-flash-001")

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[
                    Content(
                        parts=[
                            Part.from_text(text=message),
                        ]
                    )
                ],
                config=GenerateContentConfig(
                    system_instruction=self.prompt,
                    response_mime_type="application/json",
                    response_schema=ChatResponse,
                ),
            )

            if response:
                return ChatResponse(**json.loads(response.text or "{}"))
        except Exception:
            return None

        return None
