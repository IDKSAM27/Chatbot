import os
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

import PyPDF2
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    print("⚠️ pdfplumber not available, using PyPDF2 only")

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    print("⚠️ langdetect not available, defaulting to 'en'")

class CampusDocumentProcessor:
    def __init__(self, db_path: str = "campus_knowledge_base.db"):
        """Initialize document processor with SQLite database (no external dependencies)"""
        
        self.db_path = db_path
        self.init_database()
        print(f"✅ Document processor initialized with SQLite DB at: {db_path}")

    def init_database(self):
        """Initialize SQLite database for storing processed documents"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for storing FAQ data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campus_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                source_file TEXT,
                page_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for document chunks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source_file TEXT,
                page_number INTEGER,
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF with fallback methods"""
        
        extracted_data = {
            'filename': os.path.basename(pdf_path),
            'pages': [],
            'metadata': {},
            'full_text': ''
        }
        
        print(f"📖 Extracting text from: {pdf_path}")
        
        # Try pdfplumber first (better for structured content)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    extracted_data['metadata'] = {
                        'total_pages': len(pdf.pages),
                        'title': getattr(pdf.metadata, 'Title', None),
                        'author': getattr(pdf.metadata, 'Author', None)
                    }
                    
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        
                        page_data = {
                            'page_number': page_num + 1,
                            'text': page_text,
                            'tables': [],
                            'images': 0
                        }
                        
                        # Extract tables
                        tables = page.extract_tables()
                        if tables:
                            for table_idx, table in enumerate(tables):
                                table_text = self._table_to_text(table)
                                page_data['tables'].append({
                                    'table_id': table_idx,
                                    'text_representation': table_text
                                })
                                page_text += f"\n[TABLE {table_idx}]\n{table_text}"
                        
                        extracted_data['pages'].append(page_data)
                        extracted_data['full_text'] += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    
                    print(f"✅ Extracted {len(extracted_data['pages'])} pages using pdfplumber")
                    return extracted_data
                    
            except Exception as e:
                print(f"⚠️ pdfplumber failed: {e}, trying PyPDF2...")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                extracted_data['metadata'] = {
                    'total_pages': len(pdf_reader.pages),
                    'title': getattr(pdf_reader.metadata, '/Title', None) if pdf_reader.metadata else None
                }
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text() or ""
                    
                    page_data = {
                        'page_number': page_num + 1,
                        'text': page_text,
                        'tables': [],
                        'images': 0
                    }
                    
                    extracted_data['pages'].append(page_data)
                    extracted_data['full_text'] += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                print(f"✅ Extracted {len(extracted_data['pages'])} pages using PyPDF2")
                
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
        
        return extracted_data

    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table data to readable text format"""
        if not table:
            return ""
        
        text_lines = []
        for row in table:
            if row and any(cell for cell in row if cell):
                clean_row = [str(cell).strip() if cell else "" for cell in row]
                text_lines.append(" | ".join(clean_row))
        
        return "\n".join(text_lines)

    def detect_language(self, text: str) -> str:
        """Detect language with fallback"""
        if not HAS_LANGDETECT:
            # Simple heuristic for Hindi detection
            hindi_chars = set('अआइईउऊएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
            if any(char in hindi_chars for char in text):
                return 'hi'
            return 'en'
        
        try:
            return detect(text)
        except:
            return 'en'

    def parse_campus_faqs(self, text: str) -> List[Dict[str, str]]:
        """Enhanced FAQ extraction with fee-specific patterns"""

        faqs = []
        text_lower = text.lower()

        print(f"📝 Parsing {len(text)} characters of text...")
        print(f"🔍 Sample text: {text[:200]}...")

        # Clean the text first
        text = re.sub(r'\n+', '\n', text)  # Remove extra newlines
        text = re.sub(r'\s+', ' ', text)   # Normalize spaces

        # Fee-specific extraction patterns (NEW)
        if 'fee' in text_lower or 'payment' in text_lower or 'cost' in text_lower or 'tuition' in text_lower:
            print("💰 Detected fee-related content, using specialized extraction...")

            fee_patterns = [
                # Fee structure tables
                r'(?i)(.*?(?:B\.?A\.?|B\.?COM|B\.?SC|M\.?A\.?|M\.?COM|M\.?SC|B\.?TECH|M\.?TECH).*?)\s*[-–]\s*(?:Rs\.?\s*)?(\d+(?:,\d+)*)',
                # Fee amounts with course names
                r'(?i)((?:Bachelor|Master|Diploma).*?).*?(?:Rs\.?\s*|INR\s*)?(\d+(?:,\d+)*)',
                # General fee information
                r'(?i)(.*?fees?\s+for.*?)[\s:]+(?:Rs\.?\s*)?(\d+(?:,\d+)*)',
                r'(?i)(semester\s+fees?|annual\s+fees?|admission\s+fees?).*?(?:Rs\.?\s*)?(\d+(?:,\d+)*)',
            ]

            for pattern in fee_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                for match in matches:
                    if len(match) == 2:
                        course_info = match[0].strip()
                        fee_amount = match[1].strip()

                        if len(course_info) > 5 and fee_amount:
                            question = f"What is the fee for {course_info}?"
                            answer = f"The fee for {course_info} is Rs. {fee_amount}"

                            faqs.append({
                                'question': question,
                                'answer': answer,
                                'language': 'en',
                                'category': 'fees'
                            })
                            print(f"    ✅ Fee extracted: {question}")

        # Standard Q&A patterns (existing)
        qa_patterns = [
            r'(?i)Q\d*[:\.]?\s*(.*?)\s*A\d*[:\.]?\s*(.*?)(?=Q\d*[:\.]|\n\n|\Z)',
            r'(?i)(.*?\?)\s*:?\s*\n\s*(.*?)(?=\n.*?\?|\n\n|\Z)',
            r'(?i)((?:How|What|When|Where|Why).*?\?)\s*\n\s*(.*?)(?=\n(?:How|What|When|Where|Why)|\n\n|\Z)'
        ]

        for pattern_idx, pattern in enumerate(qa_patterns):
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            print(f"  Pattern {pattern_idx + 1}: Found {len(matches)} matches")

            for match in matches:
                if len(match) == 2:
                    question = match[0].strip()
                    answer = match[1].strip()

                    # Clean up
                    question = re.sub(r'[^\w\s\?\u0900-\u097F\u0600-\u06FF]', ' ', question)
                    question = re.sub(r'\s+', ' ', question).strip()
                    answer = re.sub(r'\s+', ' ', answer).strip()

                    if (len(question) > 5 and len(answer) > 20 and 
                        not question.lower().startswith(('page', 'section', 'chapter')) and
                        '?' in question):

                        faqs.append({
                            'question': question,
                            'answer': answer,
                            'language': self.detect_language(question),
                            'category': self._categorize_faq(question)
                        })
                        print(f"    ✅ Q&A: {question[:50]}...")

        # Content-based extraction (improved)
        content_sections = self._extract_content_sections(text)
        for section in content_sections:
            faqs.append(section)
            print(f"    ✅ Section: {section['question'][:50]}...")

        print(f"📊 Total extracted FAQs: {len(faqs)}")
        return faqs
    
    def _extract_content_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract structured content sections"""
        sections = []
        
        # Split text into logical sections
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 30]
        
        for paragraph in paragraphs:
            # Skip very short paragraphs
            if len(paragraph) < 50:
                continue
                
            # Create contextual questions based on content
            para_lower = paragraph.lower()
            
            if any(word in para_lower for word in ['fee', 'cost', 'payment', 'tuition']):
                if any(word in para_lower for word in ['ba', 'b.a', 'bachelor', 'bcom', 'b.com']):
                    question = "What are the fee details for undergraduate courses?"
                elif any(word in para_lower for word in ['ma', 'm.a', 'master', 'mcom', 'm.com']):
                    question = "What are the fee details for postgraduate courses?"
                else:
                    question = "What are the fee payment details?"
                    
            elif any(word in para_lower for word in ['library', 'book', 'study']):
                question = "What are the library facilities?"
                
            elif any(word in para_lower for word in ['hostel', 'mess', 'accommodation']):
                question = "What are the hostel facilities?"
                
            elif any(word in para_lower for word in ['scholarship', 'financial aid', 'छात्रवृत्ति']):
                question = "What scholarship information is available?"
                
            else:
                # Generic question based on key terms
                words = paragraph.split()[:5]
                question = f"What information is available about {' '.join(words)}?"
            
            sections.append({
                'question': question,
                'answer': paragraph,
                'language': self.detect_language(paragraph),
                'category': self._categorize_faq(paragraph)
            })
        
        return sections


    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on common words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _categorize_faq(self, question: str) -> str:
        """Categorize FAQ based on keywords"""
        question_lower = question.lower()
        
        categories = {
            'fees': ['fee', 'payment', 'cost', 'tuition', 'money', 'pay', 'charge'],
            'scholarship': ['scholarship', 'financial aid', 'grant', 'funding', 'छात्रवृत्ति'],
            'library': ['library', 'book', 'study', 'research', 'journal', 'reading'],
            'hostel': ['hostel', 'accommodation', 'mess', 'room', 'boarding', 'residential'],
            'admission': ['admission', 'application', 'eligibility', 'entrance', 'enroll'],
            'academic': ['exam', 'grade', 'semester', 'course', 'syllabus', 'class'],
            'placement': ['placement', 'job', 'career', 'internship', 'company', 'recruitment']
        }
        
        for category, keywords in categories.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
        
        return 'general'

    def process_and_store_document(self, pdf_path: str) -> bool:
        """Process PDF and store in SQLite database"""
        
        try:
            print(f"📖 Processing document: {pdf_path}")
            
            # Extract text from PDF
            doc_data = self.extract_text_from_pdf(pdf_path)
            
            if not doc_data['full_text'].strip():
                print(f"⚠️ No text extracted from {pdf_path}")
                return False
            
            # Parse FAQs from the document
            faqs = self.parse_campus_faqs(doc_data['full_text'])
            print(f"📝 Extracted {len(faqs)} FAQ items")
            
            # Store in SQLite database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for faq in faqs:
                cursor.execute('''
                    INSERT INTO campus_faqs (question, answer, category, language, source_file)
                    VALUES (?, ?, ?, ?, ?)
                ''', (faq['question'], faq['answer'], faq['category'], faq['language'], os.path.basename(pdf_path)))
            
            # Store page content chunks
            for page in doc_data['pages']:
                if page['text'].strip():
                    chunks = self._create_text_chunks(page['text'], max_length=500)
                    for chunk_idx, chunk in enumerate(chunks):
                        cursor.execute('''
                            INSERT INTO document_chunks (content, source_file, page_number, chunk_index)
                            VALUES (?, ?, ?, ?)
                        ''', (chunk, os.path.basename(pdf_path), page['page_number'], chunk_idx))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully processed and stored: {pdf_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to process {pdf_path}: {e}")
            return False

    def _create_text_chunks(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into manageable chunks"""
        
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using SQLite (keyword-based)"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple keyword-based search
            search_terms = query.lower().split()
            search_conditions = []
            search_params = []
            
            for term in search_terms:
                search_conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                search_params.extend([f"%{term}%", f"%{term}%"])
            
            search_query = f"""
                SELECT question, answer, category, language, source_file
                FROM campus_faqs 
                WHERE {' OR '.join(search_conditions)}
                ORDER BY 
                    CASE WHEN LOWER(question) LIKE ? THEN 1 ELSE 2 END,
                    LENGTH(answer)
                LIMIT ?
            """
            
            # Add priority search term and limit
            search_params.append(f"%{query.lower()}%")
            search_params.append(limit)
            
            cursor.execute(search_query, search_params)
            results = cursor.fetchall()
            
            search_results = []
            for row in results:
                result = {
                    'content': row[1],  # answer
                    'metadata': {
                        'question': row[0],
                        'category': row[2],
                        'language': row[3],
                        'source_file': row[4],
                        'doc_type': 'faq'
                    },
                    'similarity_score': self._calculate_relevance_score(query, row[0], row[1]),
                    'confidence': 'high'
                }
                search_results.append(result)
            
            conn.close()
            return search_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def _calculate_relevance_score(self, query: str, question: str, answer: str) -> float:
        """Calculate relevance score based on keyword matching"""
        query_words = set(query.lower().split())
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        question_score = len(query_words.intersection(question_words)) / len(query_words) if query_words else 0
        answer_score = len(query_words.intersection(answer_words)) / len(query_words) if query_words else 0
        
        # Weight question matches higher
        return (question_score * 0.7 + answer_score * 0.3)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total FAQs
            cursor.execute("SELECT COUNT(*) FROM campus_faqs")
            total_faqs = cursor.fetchone()[0]
            
            # Count by category
            cursor.execute("SELECT category, COUNT(*) FROM campus_faqs GROUP BY category")
            categories = dict(cursor.fetchall())
            
            # Count by language
            cursor.execute("SELECT language, COUNT(*) FROM campus_faqs GROUP BY language")
            languages = dict(cursor.fetchall())
            
            # Count chunks
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            total_chunks = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_documents': total_faqs,
                'total_chunks': total_chunks,
                'categories': categories,
                'languages': languages,
                'document_types': {'faq': total_faqs, 'content_chunk': total_chunks}
            }
            
        except Exception as e:
            print(f"❌ Statistics error: {e}")
            return {'total_documents': 0, 'categories': {}, 'languages': {}, 'document_types': {}}
