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
        """Dynamic FAQ extraction that adapts to any document structure"""

        faqs = []
        text_lower = text.lower()

        print(f"📝 Parsing {len(text)} characters of text...")
        print(f"🔍 Sample text: {text[:300]}...")

        # Dynamic fee extraction (detects patterns, doesn't hardcode values)
        if any(keyword in text_lower for keyword in ['fee', 'tuition', 'cost', 'payment', 'price']):
            print("💰 Detected fee-related content, using dynamic extraction...")

            # Extract fee information dynamically
            fee_faqs = self._extract_fee_information_dynamically(text)
            faqs.extend(fee_faqs)

        # Dynamic table extraction (for any structured data)
        table_faqs = self._extract_table_data_dynamically(text)
        faqs.extend(table_faqs)

        # Standard Q&A patterns
        qa_patterns = [
            r'(?i)Q\d*[:\.]?\s*(.*?)\s*A\d*[:\.]?\s*(.*?)(?=Q\d*[:\.]|\n\n|\Z)',
            r'(?i)(.*?\?)\s*:?\s*\n\s*(.*?)(?=\n.*?\?|\n\n|\Z)',
        ]

        for pattern_idx, pattern in enumerate(qa_patterns):
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if matches:
                print(f"  Q&A Pattern {pattern_idx + 1}: Found {len(matches)} matches")

                for match in matches:
                    if len(match) == 2:
                        question = re.sub(r'\s+', ' ', match[0].strip())
                        answer = re.sub(r'\s+', ' ', match[1].strip())

                        if len(question) > 5 and len(answer) > 20 and '?' in question:
                            faqs.append({
                                'question': question,
                                'answer': answer,
                                'language': self.detect_language(question),
                                'category': self._categorize_faq(question)
                            })

        # Content section extraction (flexible)
        content_faqs = self._extract_content_sections_dynamically(text)
        faqs.extend(content_faqs)

        print(f"📊 Total extracted FAQs: {len(faqs)}")
        return faqs

    def _extract_fee_information_dynamically(self, text: str) -> List[Dict[str, str]]:
        """Dynamically extract fee information from any format - with deduplication"""
        fee_faqs = []

        # Fee extraction patterns (same as before)
        fee_patterns = [
            r'(?i)(B\.?A\.?|B\.?COM?|B\.?SC\.?|M\.?A\.?|M\.?COM?|M\.?SC\.?|BCA|BBA|MBA|H\.?S\.?)(?:\s+.*?)?[:\s]*(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?i)(.*?(?:tuition|admission|total|annual|semester).*?fee.*?)(?:for\s+)?(B\.?A\.?|B\.?COM?|B\.?SC\.?|M\.?A\.?|M\.?COM?|M\.?SC\.?|BCA|BBA|MBA|H\.?S\.?)[:\s]*(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?i)(B\.?A\.?|B\.?COM?|B\.?SC\.?|M\.?A\.?|M\.?COM?|M\.?SC\.?|BCA|BBA|MBA|H\.?S\.?)(?:\s+[^\d\n]*?)?[:\s]+(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?i)(tuition\s+fee|admission\s+fee|total\s+fee|annual\s+fee|semester\s+fee)[^\d]*(\d+(?:,\d+)*(?:\.\d+)?)'
        ]

        found_fees = {}  # To track and prioritize fees

        for pattern_idx, pattern in enumerate(fee_patterns):
            matches = re.findall(pattern, text, re.MULTILINE)
            print(f"  Fee Pattern {pattern_idx + 1}: Found {len(matches)} matches")

            for match in matches:
                if len(match) >= 2:
                    if len(match) == 2:
                        course_or_type, amount = match[0].strip(), match[1].strip()
                        fee_type = "tuition fee"
                    elif len(match) == 3:
                        fee_type, course_or_type, amount = match[0].strip(), match[1].strip(), match[2].strip()
                    else:
                        continue
                    
                    # Clean up course name
                    course = re.sub(r'[^\w\s\.]', ' ', course_or_type).strip()
                    course = re.sub(r'\s+', ' ', course)

                    if len(course) < 2 or len(amount) < 2:
                        continue
                    
                    # Normalize course name for deduplication
                    course_normalized = course.lower().replace('.', '').replace(' ', '')

                    # Create priority system: prefer specific fee types over general ones
                    fee_key = f"{course_normalized}_fee"
                    amount_num = float(amount.replace(',', ''))

                    # Priority logic: prefer larger amounts (likely total fees) and more specific descriptions
                    priority = 0
                    if 'total' in fee_type.lower() or 'annual' in fee_type.lower():
                        priority = 3  # Highest priority for total/annual fees
                    elif 'tuition' in fee_type.lower():
                        priority = 2  # Medium priority for tuition fees
                    else:
                        priority = 1  # Lowest priority for general fees

                    # Only keep the highest priority fee for each course
                    if fee_key not in found_fees or found_fees[fee_key]['priority'] < priority:
                        found_fees[fee_key] = {
                            'course': course,
                            'amount': amount,
                            'fee_type': fee_type,
                            'priority': priority,
                            'amount_num': amount_num
                        }
                        print(f"    ✅ Updated: {course} -> Rs. {amount} (priority: {priority})")
                    else:
                        print(f"    ⏭️ Skipped: {course} -> Rs. {amount} (lower priority)")

        # Convert found_fees to FAQs
        for fee_data in found_fees.values():
            course = fee_data['course']
            amount = fee_data['amount']
            fee_type = fee_data['fee_type']

            if any(c in course.lower() for c in ['b.a', 'ba', 'b.com', 'bcom', 'b.sc', 'bsc', 'bca', 'bba', 'mba', 'h.s']):
                question = f"What is the fee for {course}?"
                answer = f"The fee for {course} is Rs. {amount}."
            else:
                question = f"What is the {course.lower()}?"
                answer = f"The {course.lower()} is Rs. {amount}."

            fee_faqs.append({
                'question': question,
                'answer': answer,
                'language': 'en',
                'category': 'fees'
            })

        print(f"💰 Dynamically extracted {len(fee_faqs)} deduplicated fee FAQs")
        return fee_faqs


    def _extract_table_data_dynamically(self, text: str) -> List[Dict[str, str]]:
        """Dynamically extract structured table data"""
        table_faqs = []

        # Look for table-like structures with numbers
        lines = text.split('\n')

        # Find lines that look like table rows (contain both text and numbers)
        table_rows = []
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and 
                re.search(r'\d+(?:\.\d+)?', line) and  # Contains numbers
                not line.isupper() and  # Not a header
                len(line.split()) >= 2):  # Has multiple parts

                table_rows.append(line)

        # Process table rows to extract meaningful information
        for row in table_rows:
            # Extract key-value pairs from table rows
            parts = re.split(r'\s{2,}|\t', row)  # Split on multiple spaces or tabs

            if len(parts) >= 2:
                key_part = parts[0].strip()
                value_parts = [p.strip() for p in parts[1:] if p.strip()]

                if value_parts and key_part:
                    # Find numeric values in the row
                    amounts = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', ' '.join(value_parts))

                    if amounts:
                        # Create FAQ based on the structure
                        if any(word in key_part.lower() for word in ['fee', 'cost', 'amount', 'price']):
                            question = f"What is the {key_part.lower()}?"
                            answer = f"The {key_part.lower()} is Rs. {amounts[0]}."

                            table_faqs.append({
                                'question': question,
                                'answer': answer,
                                'language': 'en',
                                'category': self._categorize_faq(key_part)
                            })
                            print(f"    📊 Table: {key_part} -> Rs. {amounts[0]}")

        print(f"📋 Dynamically extracted {len(table_faqs)} table FAQs")
        return table_faqs

    def _extract_content_sections_dynamically(self, text: str) -> List[Dict[str, str]]:
        """Dynamically extract content sections based on structure"""
        section_faqs = []

        # Split text into logical sections
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30]

        for paragraph in paragraphs:
            # Skip very long paragraphs (likely full text dumps)
            if len(paragraph) > 500:
                continue
            
            # Extract key topics from the paragraph
            key_terms = self._extract_key_terms(paragraph)

            if key_terms:
                # Create contextual question based on key terms
                if len(key_terms) == 1:
                    question = f"What information is available about {key_terms[0]}?"
                else:
                    question = f"What are the details for {', '.join(key_terms[:2])}?"

                section_faqs.append({
                    'question': question,
                    'answer': paragraph[:400] + "..." if len(paragraph) > 400 else paragraph,
                    'language': self.detect_language(paragraph),
                    'category': self._categorize_faq(' '.join(key_terms))
                })
                print(f"    📄 Section: {question[:50]}...")

        print(f"📑 Dynamically extracted {len(section_faqs)} content sections")
        return section_faqs

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text to generate questions"""

        # Common important terms for educational documents
        important_terms = {
            'fees': ['fee', 'tuition', 'cost', 'payment', 'amount'],
            'courses': ['b.a', 'b.com', 'b.sc', 'bca', 'bba', 'mba', 'course', 'program'],
            'facilities': ['library', 'lab', 'hostel', 'mess', 'campus'],
            'academic': ['exam', 'admission', 'semester', 'year', 'subject'],
            'administration': ['registration', 'enrollment', 'identity', 'card']
        }

        text_lower = text.lower()
        found_terms = []

        for category, terms in important_terms.items():
            for term in terms:
                if term in text_lower and term not in found_terms:
                    found_terms.append(term)

        return found_terms[:3]  # Return top 3 terms

    
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
        """Enhanced search with better keyword matching and course name recognition"""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Normalize query for better matching
            query_lower = query.lower().strip()
            print(f"🔍 Original query: '{query}' -> Normalized: '{query_lower}'")

            # Extract course names from query
            course_keywords = self._extract_course_from_query(query_lower)
            fee_keywords = self._extract_fee_type_from_query(query_lower)

            print(f"📚 Detected courses: {course_keywords}")
            print(f"💰 Detected fee types: {fee_keywords}")

            # Build search query with course-specific matching
            search_conditions = []
            search_params = []

            if course_keywords:
                # Prioritize exact course matches
                for course in course_keywords:
                    # Direct question match
                    search_conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                    search_params.extend([f"%{course}%", f"%{course}%"])

            if fee_keywords:
                # Add fee type matching
                for fee_type in fee_keywords:
                    search_conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                    search_params.extend([f"%{fee_type}%", f"%{fee_type}%"])

            # Fallback: general keyword search
            if not search_conditions:
                query_words = query_lower.split()
                for word in query_words:
                    if len(word) > 2:  # Skip very short words
                        search_conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                        search_params.extend([f"%{word}%", f"%{word}%"])

            if not search_conditions:
                return []

            # Execute search with priority scoring
            search_query = f"""
                SELECT question, answer, category, language, source_file
                FROM campus_faqs 
                WHERE {' OR '.join(search_conditions)}
                ORDER BY 
                    CASE 
                        WHEN LOWER(question) LIKE ? THEN 1
                        WHEN LOWER(answer) LIKE ? THEN 2
                        ELSE 3 
                    END,
                    LENGTH(answer)
                LIMIT ?
            """

            # Add priority search terms (first course/fee keyword) and limit
            if course_keywords:
                priority_term = course_keywords[0]
            elif fee_keywords:
                priority_term = fee_keywords[0]
            else:
                priority_term = query_lower.split()[0] if query_lower.split() else query_lower

            search_params.extend([f"%{priority_term}%", f"%{priority_term}%", limit])

            cursor.execute(search_query, search_params)
            results = cursor.fetchall()

            search_results = []
            for row in results:
                question, answer, category, language, source_file = row

                # Calculate relevance score based on exact matches
                relevance_score = self._calculate_enhanced_relevance(query_lower, question, answer, course_keywords, fee_keywords)

                result = {
                    'content': answer,
                    'metadata': {
                        'question': question,
                        'category': category,
                        'language': language,
                        'source_file': source_file,
                        'doc_type': 'faq'
                    },
                    'similarity_score': relevance_score,
                    'confidence': 'high' if relevance_score > 0.7 else 'medium' if relevance_score > 0.4 else 'low'
                }
                search_results.append(result)

                print(f"  Found: {question} (score: {relevance_score:.2f})")

            # Sort by relevance score (highest first)
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)

            conn.close()
            print(f"✅ Returning {len(search_results)} results")
            return search_results

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
        
    def _extract_course_from_query(self, query: str) -> List[str]:
        """Extract course names from user query"""
        courses = []

        # Course mapping for various formats
        course_patterns = {
            'b.a': ['b.a', 'ba', 'bachelor of arts', 'arts'],
            'b.sc': ['b.sc', 'bsc', 'bachelor of science', 'science'],
            'b.com': ['b.com', 'bcom', 'bachelor of commerce', 'commerce'],
            'bca': ['bca', 'bachelor of computer application'],
            'bba': ['bba', 'bachelor of business administration'],
            'mba': ['mba', 'master of business administration'],
            'h.s': ['h.s', 'hs', 'higher secondary'],
        }

        for standard_name, variations in course_patterns.items():
            for variation in variations:
                if variation in query:
                    courses.append(standard_name)
                    break  # Only add once per course
                
        return courses
    
    def _extract_fee_type_from_query(self, query: str) -> List[str]:
        """Extract fee type from user query"""
        fee_types = []

        fee_patterns = {
            'tuition': ['tuition', 'tuition fee'],
            'admission': ['admission', 'admission fee'],
            'total': ['total', 'total fee', 'overall'],
            'fees': ['fee', 'fees', 'cost', 'amount']
        }

        for fee_type, variations in fee_patterns.items():
            for variation in variations:
                if variation in query:
                    fee_types.append(fee_type)
                    break
                
        return fee_types

    def _calculate_enhanced_relevance(self, query: str, question: str, answer: str, course_keywords: List[str], fee_keywords: List[str]) -> float:
        """Calculate relevance score with course and fee type weighting"""
        
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        score = 0.0
        
        # Course matching (high weight)
        for course in course_keywords:
            if course in question_lower:
                score += 0.5  # High score for course in question
            elif course in answer_lower:
                score += 0.3  # Medium score for course in answer
        
        # Fee type matching (medium weight)
        for fee_type in fee_keywords:
            if fee_type in question_lower:
                score += 0.3
            elif fee_type in answer_lower:
                score += 0.2
        
        # General keyword matching (low weight)
        query_words = set(query.split())
        question_words = set(question_lower.split())
        answer_words = set(answer_lower.split())
        
        question_overlap = len(query_words.intersection(question_words)) / len(query_words) if query_words else 0
        answer_overlap = len(query_words.intersection(answer_words)) / len(query_words) if query_words else 0
        
        score += question_overlap * 0.2
        score += answer_overlap * 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)

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
