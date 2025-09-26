import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from werkzeug.utils import secure_filename

from ..app import app
from ..utils.document_processor import CampusDocumentProcessor

# Initialize document processor
doc_processor = CampusDocumentProcessor()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/documents')
@login_required
def document_management():
    """Document management page"""
    stats = doc_processor.get_statistics()
    return render_template('admin/documents.html', stats=stats)

@app.route('/admin/upload_document', methods=['POST'])
@login_required  
def upload_document():
    """Enhanced document upload with better processing"""
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('document_management'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('document_management'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            print(f"\nProcessing uploaded file: {filename}")
            
            # Extract text first to see what we're working with
            doc_data = doc_processor.extract_text_from_pdf(filepath)
            print(f"Extracted {len(doc_data['full_text'])} characters from PDF")
            
            if len(doc_data['full_text']) < 100:
                flash(f'Warning: Very little text extracted from {filename}. File might be image-based or corrupted.', 'warning')
                return redirect(url_for('document_management'))
            
            # Show a preview of extracted text
            preview = doc_data['full_text'][:500] + "..." if len(doc_data['full_text']) > 500 else doc_data['full_text']
            print(f"Text preview: {preview}")
            
            # Process and store
            success = doc_processor.process_and_store_document(filepath)
            
            if success:
                # Get stats to show what was extracted
                import sqlite3
                conn = sqlite3.connect(doc_processor.db_path)
                cursor = conn.cursor()
                
                # Count FAQs from this file
                cursor.execute("SELECT COUNT(*) FROM campus_faqs WHERE source_file = ?", (filename,))
                faq_count = cursor.fetchone()[0]
                
                # Get sample FAQs
                cursor.execute("SELECT question, category FROM campus_faqs WHERE source_file = ? LIMIT 3", (filename,))
                sample_faqs = cursor.fetchall()
                
                conn.close()
                
                flash(f'Successfully processed {filename}! Extracted {faq_count} FAQ items.', 'success')
                
                if sample_faqs:
                    sample_list = ", ".join([f"{faq[0][:50]}..." for faq in sample_faqs])
                    flash(f'Sample FAQs: {sample_list}', 'info')
                else:
                    flash('No structured FAQs found. The content was stored as general text chunks.', 'warning')
                
            else:
                flash(f'Failed to process {filename}', 'error')
                
        except Exception as e:
            flash(f'Error processing document: {str(e)}', 'error')
            print(f"Processing error: {e}")
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
    else:
        flash('Invalid file type. Please upload PDF, DOCX, or TXT files.', 'error')
    
    return redirect(url_for('document_management'))

@app.route('/admin/clear_knowledge_base', methods=['POST'])
@login_required
def clear_knowledge_base():
    """Clear all stored documents (for testing)"""
    try:
        import sqlite3
        conn = sqlite3.connect(doc_processor.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM campus_faqs")
        cursor.execute("DELETE FROM document_chunks")
        
        conn.commit()
        conn.close()
        
        flash('Knowledge base cleared successfully!', 'success')
    except Exception as e:
        flash(f'Error clearing knowledge base: {str(e)}', 'error')
    
    return redirect(url_for('document_management'))

@app.route('/api/v1/search_documents')
@login_required
def search_documents():
    """API endpoint to search processed documents"""
    
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 5))
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    try:
        results = doc_processor.search_documents(query, limit=limit)
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/search/<query>')
@login_required
def debug_search(query):
    """Debug endpoint to see search results"""
    results = doc_processor.search_documents(query, limit=5)
    
    debug_info = {
        'query': query,
        'total_results': len(results),
        'results': []
    }
    
    for result in results:
        debug_info['results'].append({
            'question': result['metadata']['question'],
            'answer': result['content'][:100] + "...",
            'score': result['similarity_score'],
            'category': result['metadata']['category']
        })
    
    return jsonify(debug_info)
