from src.utils.document_processor import CampusDocumentProcessor

def test_flexible_extraction():
    """Test the flexible, dynamic extraction"""
    
    # Test with different formats of fee data
    test_cases = [
        # Your PDF format
        """
        Fees structure for H.S. and B.A., B.Sc., B.Com.
        B.A. 720.00
        B.Sc. 840.00  
        B.Com. 3000.00
        H.S. 600.00
        """,
        
        # Different format
        """
        Course Fees:
        Bachelor of Arts (B.A.): Rs. 15000
        Bachelor of Commerce: Rs. 18000
        Master of Science: Rs. 25000
        """,
        
        # Another format
        """
        Annual Tuition Fee
        BCA - Rs.26,000
        BBA - Rs.25,000
        MBA - Rs.45,000
        """
    ]
    
    processor = CampusDocumentProcessor()
    
    # Clear existing data
    import sqlite3
    conn = sqlite3.connect(processor.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campus_faqs")
    conn.commit()
    conn.close()
    
    # Test each format
    for i, test_text in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"TESTING FORMAT {i+1}")
        print('='*50)
        
        faqs = processor.parse_campus_faqs(test_text)
        
        # Show what was extracted
        for faq in faqs:
            print(f"Q: {faq['question']}")
            print(f"A: {faq['answer']}")
            print(f"Category: {faq['category']}")
            print("-" * 30)

if __name__ == "__main__":
    test_flexible_extraction()
