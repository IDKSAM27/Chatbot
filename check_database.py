import sqlite3

def check_stored_data():
    """Check what's actually stored in the database"""
    
    try:
        conn = sqlite3.connect('campus_knowledge_base.db')
        cursor = conn.cursor()
        
        # Count total FAQs
        cursor.execute("SELECT COUNT(*) FROM campus_faqs")
        total = cursor.fetchone()[0]
        print(f"📊 Total FAQs in database: {total}")
        
        # Show sample FAQs
        cursor.execute("SELECT question, answer, category, source_file FROM campus_faqs LIMIT 5")
        faqs = cursor.fetchall()
        
        print(f"\n📝 Sample FAQs:")
        for i, (question, answer, category, source) in enumerate(faqs, 1):
            print(f"{i}. Q: {question}")
            print(f"   A: {answer[:100]}...")
            print(f"   Category: {category}, Source: {source}")
            print("-" * 50)
        
        # Count by category
        cursor.execute("SELECT category, COUNT(*) FROM campus_faqs GROUP BY category")
        categories = cursor.fetchall()
        
        print(f"\n📈 FAQs by category:")
        for category, count in categories:
            print(f"  {category}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_stored_data()
