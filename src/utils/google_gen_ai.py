import json
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from .document_processor import CampusDocumentProcessor

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
        
        # Initialize document processor for knowledge retrieval
        self.doc_processor = CampusDocumentProcessor()

    def refresh_prompt(self):
        try:
            with open("src/utils/prompt.txt", 'r', encoding='utf-8') as file:
                self.prompt = file.read().strip()
                if not self.prompt:
                    self.prompt = "You are a helpful campus assistant. Respond helpfully to student queries."
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Error reading prompt file: {e}")
            self.prompt = """You are a helpful campus assistant for Indian colleges and universities. 
            Help students with fees, scholarships, timetables, and campus information. 
            Keep responses concise and student-friendly."""

    def search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Enhanced knowledge base search that uses the best match only"""
        try:
            print(f"Searching knowledge base for: {query}")
            results = self.doc_processor.search_documents(query, limit=3)

            if not results:
                print("No results found in knowledge base")
                return {
                    'has_context': False,
                    'context': "No specific campus information found for this query.",
                    'sources': []
                }

            # Filter for high-quality results
            relevant_results = [r for r in results if r['similarity_score'] > 0.2]

            if not relevant_results:
                print("No relevant results found")
                return {
                    'has_context': False,
                    'context': "No relevant campus information found.",
                    'sources': []
                }

            print(f"Found {len(relevant_results)} relevant results")

            # USE ONLY THE BEST RESULT (highest score)
            best_result = relevant_results[0]

            # Get the exact question and answer from the best match
            best_question = best_result['metadata']['question']
            best_answer = best_result['content'].strip()

            # Create focused context using the best match
            context = f"Question: {best_question}\nAnswer: {best_answer}"

            print(f"    Best Match: {best_question} (score: {best_result['similarity_score']:.2f})")
            print(f"      Answer: {best_answer[:50]}...")

            return {
                'has_context': True,
                'context': context,
                'best_question': best_question,
                'best_answer': best_answer,
                'sources': [{
                    'category': best_result['metadata'].get('category', 'general'),
                    'score': best_result['similarity_score'],
                    'source_file': best_result['metadata'].get('source_file', 'unknown')
                }],
                'total_results': len(relevant_results)
            }
        
        except Exception as e:
            print(f"Knowledge search error: {e}")
            return {
                'has_context': False,
                'context': "Knowledge base search temporarily unavailable.",
                'sources': []
            }


    def chat(self, message: str) -> Optional[ChatResponse]:
        """Enhanced chat with direct answer from best match"""

        if not self.prompt:
            self.refresh_prompt()

        print(f"Processing message: {message}")

        # Search knowledge base for relevant information
        kb_result = self.search_knowledge_base(message)

        if kb_result['has_context']:
            # Use the best match directly
            best_answer = kb_result.get('best_answer', '')
            best_question = kb_result.get('best_question', '')

            # Create a focused prompt that prioritizes the exact match
            enhanced_prompt = f"""
You are a campus assistant with access to official college documents.

OFFICIAL CAMPUS INFORMATION (USE THIS EXACTLY):
The user asked: "{message}"
From our documents: {best_question}
Official Answer: {best_answer}

INSTRUCTIONS:
1. Use the official answer above as your PRIMARY and MAIN response
2. Start with "According to our campus documents,"
3. Give the specific information from the official answer
4. If the question is in Hindi, respond in Hindi
5. If the question is in English, respond in English
6. Keep the response direct and factual
7. DO NOT add extra information not in the official answer

User Question: {message}

Provide the official answer from the campus documents:
"""

            print(f"Using direct match: {best_question}")

        else:
            # Fallback prompt when no specific context is found
            enhanced_prompt = f"""
{self.prompt}

Student Question: {message}

No specific campus information was found for this query. Provide general helpful guidance for Indian college students, but mention that for specific campus details, they should check with their college office.

Please provide a helpful response:
"""
    
        try:
            print(f"Sending to Gemini...")

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=enhanced_prompt
            )

            if response and response.text:
                clean_response = response.text.strip()
                print(f"Generated response: {clean_response[:100]}...")
                return ChatResponse(response=clean_response)
            else:
                print("No response from Gemini")
                # If AI fails but we have campus context, return it directly
                if kb_result['has_context']:
                    direct_response = f"According to our campus documents, {kb_result.get('best_answer', '')}"
                    return ChatResponse(response=direct_response)
                return None

        except Exception as e:
            print(f"Gemini API Error: {e}")
            # Fallback to document-only response if AI fails
            if kb_result['has_context']:
                fallback_response = f"According to our campus documents: {kb_result.get('best_answer', '')}"
                return ChatResponse(response=fallback_response)
            return None
