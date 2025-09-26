import json
import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

class ChatResponse(BaseModel):
    response: Optional[str] = None

class GoogleAPIHandler:
    def __init__(self):
        self.gemini_api_key = GEMINI_API_KEY
        if not self.gemini_api_key:
            raise ValueError("GEMINI_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=self.gemini_api_key)
        self.prompt = ""

    def refresh_prompt(self):
        try:
            # Fix encoding issue - use UTF-8 explicitly
            with open("src/utils/prompt.txt", 'r', encoding='utf-8') as file:
                self.prompt = file.read().strip()
                if not self.prompt:
                    self.prompt = "You are a helpful campus assistant. Respond helpfully to student queries."
                    
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Error reading prompt file: {e}")
            # Fallback prompt for campus assistant
            self.prompt = """You are a helpful campus assistant for Indian colleges and universities. 
            Help students with fees, scholarships, timetables, and campus information. 
            Keep responses concise and student-friendly."""

    def chat(self, message: str) -> Optional[ChatResponse]:
        try:
            if not self.prompt:
                self.refresh_prompt()
            
            # Create full prompt with context
            full_prompt = f"""
{self.prompt}

Student Question: {message}

Please provide a helpful, concise response for this campus-related query. If the question is in Hindi or another Indian language, respond in the same language.
"""
            
            print(f"DEBUG: Sending to Gemini API...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            
            if response and response.text:
                clean_response = response.text.strip()
                print(f"DEBUG: Received response: {clean_response[:100]}...")
                return ChatResponse(response=clean_response)
            else:
                print("DEBUG: No response text from Gemini")
                return None
                
        except Exception as e:
            print(f"Gemini API Error: {e}")
            import traceback
            print(f"Gemini Traceback: {traceback.format_exc()}")
            return None
