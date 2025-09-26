import traceback
from flask import jsonify, request
from flask_login import login_required, current_user
from ....utils.google_gen_ai import GoogleAPIHandler
from ....models import Sessions, Messages
from ....app import db
from ....app import VERSION
from ...api import v1_router

__all__ = ("read_root",)

@v1_router.get("/")
def read_root():
    data = {"message": "Language Agnostic Chatbot", "status": "OK", "version": VERSION}
    return jsonify(data)

@v1_router.post('/chat')
@login_required
def chat_endpoint():
    """Main chat API endpoint for multilingual campus assistant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        print(f"DEBUG: Received message: {message}")  # Debug log
        
        # Get or create user session
        user_session = Sessions.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if not user_session:
            user_session = Sessions(user_id=current_user.id)
            db.session.add(user_session)
            db.session.commit()
            print(f"DEBUG: Created new session: {user_session.id}")
        
        # Save user message to database
        user_msg = Messages(
            session_id=user_session.id, 
            sender='user', 
            text=message
        )
        db.session.add(user_msg)
        db.session.commit()
        print(f"DEBUG: Saved user message")
        
        # Get AI response using your existing GoogleAPIHandler
        print(f"DEBUG: Calling AI handler...")
        ai_handler = GoogleAPIHandler()
        ai_handler.refresh_prompt()
        
        # Check if prompt loaded
        if not ai_handler.prompt:
            return jsonify({
                'response': 'I apologize, my knowledge base is currently updating. Please try again in a moment.',
                'status': 'error'
            }), 500
        
        print(f"DEBUG: Prompt loaded: {len(ai_handler.prompt)} characters")
        
        response = ai_handler.chat(message)
        print(f"DEBUG: AI response: {response}")
        
        if response and response.response:
            # Save bot response to database
            bot_msg = Messages(
                session_id=user_session.id, 
                sender='bot', 
                text=response.response
            )
            db.session.add(bot_msg)
            db.session.commit()
            print(f"DEBUG: Saved bot response")
            
            return jsonify({
                'response': response.response,
                'session_id': user_session.id,
                'status': 'success'
            })
        else:
            print(f"DEBUG: No response from AI handler")
            return jsonify({
                'response': 'I apologize, but I encountered an issue processing your request. Please try again.',
                'status': 'error'
            }), 500
            
    except Exception as e:
        # Print full traceback for debugging
        print(f"ERROR in chat_endpoint: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        
        return jsonify({
            'response': f'Sorry, I encountered a technical issue: {str(e)}',
            'status': 'error'
        }), 500