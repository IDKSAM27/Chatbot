import sqlite3
from datetime import datetime

def populate_sample_faqs():
    """Add sample campus FAQ data for demo"""
    
    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()
    
    # Create FAQ table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campus_faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            question_en TEXT NOT NULL,
            question_hi TEXT,
            answer_en TEXT NOT NULL,
            answer_hi TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    sample_faqs = [
        {
            'category': 'Fees',
            'question_en': 'How do I pay semester fees online?',
            'question_hi': 'मैं सेमेस्टर फीस ऑनलाइन कैसे भरूं?',
            'answer_en': 'Visit the college portal, login with your student ID, go to Fee Payment section, select semester, choose payment method (net banking/UPI/card), and complete payment. Save the receipt.',
            'answer_hi': 'कॉलेज पोर्टल पर जाएं, अपनी स्टूडेंट आईडी से लॉगिन करें, फी पेमेंट सेक्शन में जाएं, सेमेस्टर चुनें, पेमेंट मेथड चुनें और पेमेंट पूरा करें।',
            'keywords': 'fees, payment, online, semester, portal'
        },
        {
            'category': 'Scholarships',
            'question_en': 'What scholarships are available for students?',
            'question_hi': 'छात्रों के लिए कौन सी छात्रवृत्तियां उपलब्ध हैं?',
            'answer_en': 'Merit scholarships, need-based aid, SC/ST scholarships, and minority scholarships are available. Apply through NSP portal or visit Student Affairs Office.',
            'answer_hi': 'मेरिट स्कॉलरशिप, आवश्यकता आधारित सहायता, SC/ST छात्रवृत्ति उपलब्ध हैं। NSP पोर्टल या स्टूडेंट अफेयर्स ऑफिस से संपर्क करें।',
            'keywords': 'scholarship, financial aid, NSP, student affairs'
        },
        {
            'category': 'Library',
            'question_en': 'What are the library timings?',
            'question_hi': 'लाइब्रेरी का समय क्या है?',
            'answer_en': 'Library is open 9 AM to 8 PM on weekdays, 10 AM to 5 PM on weekends. Extended hours during exams.',
            'answer_hi': 'लाइब्रेरी सप्ताह में 9 बजे से 8 बजे तक, सप्ताहांत में 10 बजे से 5 बजे तक खुली है। परीक्षा के दौरान अधिक समय।',
            'keywords': 'library, timings, hours, books, study'
        }
    ]
    
    for faq in sample_faqs:
        cursor.execute('''
            INSERT OR REPLACE INTO campus_faqs 
            (category, question_en, question_hi, answer_en, answer_hi, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            faq['category'], faq['question_en'], faq['question_hi'],
            faq['answer_en'], faq['answer_hi'], faq['keywords']
        ))
    
    conn.commit()
    conn.close()
    print("Sample FAQ data populated successfully!")

if __name__ == "__main__":
    populate_sample_faqs()
