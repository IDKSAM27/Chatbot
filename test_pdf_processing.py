from src.utils.document_processor import CampusDocumentProcessor

def test_with_sample_data():
    """Test document processing with sample campus data"""
    
    print("🚀 Testing Campus Document Processor...")
    processor = CampusDocumentProcessor()
    
    # Create sample campus text (simulate PDF content)
    sample_campus_text = """
    COLLEGE FEE STRUCTURE 2025
    
    Q1. How do I pay semester fees online?
    A1. Visit the college portal at portal.college.edu, login with your student ID, 
        navigate to 'Fee Payment' section, select your semester, choose payment method 
        (net banking/UPI/debit card), and complete the payment. Save the receipt.
    
    Q2. What is the fee payment deadline for this semester?
    A2. Fee payment deadline is 15th of every month. Late payment attracts a penalty 
        of Rs. 500 per day. Payment can be done online or at the accounts office.
    
    SCHOLARSHIP INFORMATION
    
    मैं छात्रवृत्ति के लिए कैसे आवेदन करूं?
    छात्रवृत्ति के लिए राष्ट्रीय छात्रवृत्ति पोर्टल (NSP) पर जाएं या छात्र कार्यालय से संपर्क करें।
    आवश्यक दस्तावेज: आय प्रमाण पत्र, जाति प्रमाण पत्र, बैंक विवरण।
    
    LIBRARY FACILITIES
    
    Library Timings: Monday to Friday: 9:00 AM to 8:00 PM, Saturday: 10:00 AM to 5:00 PM
    Book Issue: Maximum 3 books for 15 days. Renewal possible if no other reservations.
    Digital Resources: Access to online journals and e-books through college network.
    
    HOSTEL INFORMATION  
    
    Mess Timings:
    Breakfast: 7:30 AM - 9:30 AM
    Lunch: 12:30 PM - 2:30 PM  
    Dinner: 7:30 PM - 9:30 PM
    
    Room Allocation: Based on merit and availability. Applications open in June.
    """
    
    # Parse FAQs from sample text
    faqs = processor.parse_campus_faqs(sample_campus_text)
    
    print(f"📝 Extracted {len(faqs)} FAQ items:")
    for i, faq in enumerate(faqs[:5]):  # Show first 5
        print(f"\n{i+1}. Category: {faq['category']}")
        print(f"   Question: {faq['question']}")
        print(f"   Answer: {faq['answer'][:100]}...")
        print(f"   Language: {faq['language']}")
    
    # Test search functionality
    print("\n🔍 Testing search functionality:")
    test_queries = [
        "How to pay fees online?",
        "scholarship information",
        "Library timings",
        "Mess schedule"
    ]
    
    # First simulate storing the data
    import sqlite3
    conn = sqlite3.connect(processor.db_path)
    cursor = conn.cursor()
    
    for faq in faqs:
        cursor.execute('''
            INSERT INTO campus_faqs (question, answer, category, language, source_file)
            VALUES (?, ?, ?, ?, ?)
        ''', (faq['question'], faq['answer'], faq['category'], faq['language'], 'test_document.pdf'))
    
    conn.commit()
    conn.close()
    
    # Now test search
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = processor.search_documents(query, limit=2)
        if results:
            for result in results:
                print(f"  Found: {result['content'][:100]}...")
                print(f"  Category: {result['metadata']['category']}")
                print(f"  Score: {result['similarity_score']:.2f}")
        else:
            print("  No matches found")
    
    # Show statistics
    stats = processor.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total FAQs: {stats['total_documents']}")
    print(f"  Categories: {stats['categories']}")
    print(f"  Languages: {stats['languages']}")

if __name__ == "__main__":
    test_with_sample_data()
