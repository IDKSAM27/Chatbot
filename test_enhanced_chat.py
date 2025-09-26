from src.utils.google_gen_ai import GoogleAPIHandler
from src.utils.document_processor import CampusDocumentProcessor

def test_enhanced_chat():
    """Test the enhanced chat with document context"""
    
    print("🚀 Testing Enhanced Chat with Document Context")
    
    # First, populate some test data
    processor = CampusDocumentProcessor()
    
    # Add some structured FAQ data
    import sqlite3
    conn = sqlite3.connect(processor.db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM campus_faqs")
    
    # Add better structured FAQs
    test_faqs = [
        {
            'question': 'How do I pay semester fees online?',
            'answer': 'To pay semester fees online: 1) Visit college portal at portal.college.edu 2) Login with student ID 3) Go to Fee Payment section 4) Select semester 5) Choose payment method (Net Banking/UPI/Card) 6) Complete payment and save receipt. Fee deadline is 15th of each month.',
            'category': 'fees',
            'language': 'en'
        },
        {
            'question': 'What are the library timings?',
            'answer': 'Library Timings: Monday to Friday: 9:00 AM to 8:00 PM, Saturday: 10:00 AM to 5:00 PM, Sunday: Closed. During exam periods, library extends hours to 10:00 PM. Students can issue maximum 3 books for 15 days.',
            'category': 'library',
            'language': 'en'
        },
        {
            'question': 'छात्रवृत्ति के लिए कैसे आवेदन करें?',
            'answer': 'छात्रवृत्ति के लिए आवेदन: 1) राष्ट्रीय छात्रवृत्ति पोर्टल (NSP) पर जाएं 2) छात्र कार्यालय से संपर्क करें 3) आवश्यक दस्तावेज: आय प्रमाण पत्र, जाति प्रमाण पत्र, बैंक विवरण 4) आवेदन की अंतिम तिथि: 30 सितंबर',
            'category': 'scholarship',
            'language': 'hi'
        },
        {
            'question': 'What are the hostel mess timings?',
            'answer': 'Hostel Mess Timings: Breakfast: 7:30 AM - 9:30 AM, Lunch: 12:30 PM - 2:30 PM, Evening Snacks: 4:30 PM - 5:30 PM, Dinner: 7:30 PM - 9:30 PM. Weekly menu is posted on hostel notice board. Special diet available for medical conditions.',
            'category': 'hostel',
            'language': 'en'
        }
    ]
    
    for faq in test_faqs:
        cursor.execute('''
            INSERT INTO campus_faqs (question, answer, category, language, source_file)
            VALUES (?, ?, ?, ?, ?)
        ''', (faq['question'], faq['answer'], faq['category'], faq['language'], 'test_document.pdf'))
    
    conn.commit()
    conn.close()
    
    # Test the enhanced chat
    handler = GoogleAPIHandler()
    
    test_queries = [
        "How do I pay my semester fees?",
        "Library timings?",
        "छात्रवृत्ति कैसे मिलेगी?",
        "Mess timings?",
        "What about exam schedule?"  # This should show no context found
    ]
    
    print("\n" + "="*50)
    print("TESTING ENHANCED CHAT RESPONSES")
    print("="*50)
    
    for query in test_queries:
        print(f"\n💬 Query: {query}")
        print("-" * 30)
        
        response = handler.chat(query)
        if response and response.response:
            print(f"🤖 Response: {response.response}")
        else:
            print("❌ No response generated")
        
        print("-" * 30)

if __name__ == "__main__":
    test_enhanced_chat()
