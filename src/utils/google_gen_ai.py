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
        """Enhanced knowledge base search with better context"""
        try:
            print(f"🔍 Searching knowledge base for: {query}")
            results = self.doc_processor.search_documents(query, limit=5)
            
            if not results:
                print("❌ No results found in knowledge base")
                return {
                    'has_context': False,
                    'context': "No specific campus information found for this query.",
                    'sources': []
                }
            
            # Filter for high-quality results
            relevant_results = [r for r in results if r['similarity_score'] > 0.2]
            
            if not relevant_results:
                print("❌ No relevant results found")
                return {
                    'has_context': False,
                    'context': "No relevant campus information found.",
                    'sources': []
                }
            
            print(f"✅ Found {len(relevant_results)} relevant results")
            
            # Build comprehensive context
            context_parts = []
            sources = []
            
            for i, result in enumerate(relevant_results[:3]):  # Top 3 results
                score = result['similarity_score']
                content = result['content'].strip()
                metadata = result['metadata']
                
                # Clean up content
                if len(content) > 300:
                    content = content[:300] + "..."
                
                context_parts.append(f"• {content}")
                sources.append({
                    'category': metadata.get('category', 'general'),
                    'score': score,
                    'source_file': metadata.get('source_file', 'unknown')
                })
                
                print(f"  Result {i+1}: {metadata.get('category', 'N/A')} (score: {score:.2f})")
            
            context = "\n".join(context_parts)
            
            return {
                'has_context': True,
                'context': context,
                'sources': sources,
                'total_results': len(relevant_results)
            }
            
        except Exception as e:
            print(f"❌ Knowledge search error: {e}")
            return {
                'has_context': False,
                'context': f"Knowledge base search error: {str(e)}",
                'sources': []
            }

    def chat(self, message: str) -> Optional[ChatResponse]:
        """Enhanced chat with prominent document context"""
        
        if not self.prompt:
            self.refresh_prompt()
        
        print(f"💬 Processing message: {message}")
        
        # Search knowledge base for relevant information
        kb_result = self.search_knowledge_base(message)
        
        if kb_result['has_context']:
            # Create context-heavy prompt when we have good information
            enhanced_prompt = f"""
You are a campus assistant with access to official college documents. You MUST prioritize and use the official campus information provided below.

OFFICIAL CAMPUS INFORMATION (USE THIS FIRST):
{kb_result['context']}

INSTRUCTIONS:
1. ALWAYS use the official campus information above as your PRIMARY source
2. Base your answer directly on the campus information provided
3. If the campus information fully answers the question, use it and add "According to our campus documents..." 
4. If the question is in Hindi, respond in Hindi
5. If the question is in English, respond in English
6. Keep responses specific and actionable
7. Do NOT provide generic answers when campus information is available

Student Question: {message}

Provide a response based primarily on the official campus information above:
"""
        else:
            # Fallback prompt when no specific context is found
            enhanced_prompt = f"""
{self.prompt}

Student Question: {message}

Note: No specific campus information was found for this query. Provide general helpful guidance for Indian college students, but mention that for specific campus details, they should check with their college office.

Please provide a helpful response:
"""
        
        try:
            print(f"🤖 Sending to Gemini with {'campus context' if kb_result['has_context'] else 'general context'}...")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=enhanced_prompt
            )
            
            if response and response.text:
                clean_response = response.text.strip()
                print(f"✅ Generated response with {'document context' if kb_result['has_context'] else 'general guidance'}")
                return ChatResponse(response=clean_response)
            else:
                print("❌ No response from Gemini")
                # If AI fails but we have campus context, return it directly
                if kb_result['has_context']:
                    return ChatResponse(response=f"According to our campus documents:\n\n{kb_result['context']}")
                return None
                
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            # Fallback to document-only response if AI fails
            if kb_result['has_context']:
                fallback_response = f"Based on our campus information:\n\n{kb_result['context']}\n\nFor more details, please contact the relevant campus office."
                return ChatResponse(response=fallback_response)
            return None
