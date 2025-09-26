import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def test_gemini_simple():
    """Test Gemini API with simple call"""
    try:
        api_key = os.getenv("GEMINI_KEY")
        if not api_key:
            print("❌ GEMINI_KEY not found in environment")
            return
            
        print(f"✅ API Key found: {api_key[:10]}...")
        
        client = genai.Client(api_key=api_key)
        print("✅ Client created successfully")
        
        # Simple test without complex schemas
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents="Hello, how are you?"
        )
        
        print(f"✅ Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_gemini_simple()
