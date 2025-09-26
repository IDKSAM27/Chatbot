from flask import render_template, jsonify
from flask_login import login_required
from ..app import app, db
from ..models import Sessions, Messages, Users
from sqlalchemy import func

@app.get('/admin/')
@login_required  
def admin_dashboard():
    """Admin dashboard for monitoring chatbot usage"""
    
    # Get statistics
    total_sessions = Sessions.query.count()
    total_messages = Messages.query.count()
    active_sessions = Sessions.query.filter_by(is_active=True).count()
    total_users = Users.query.count()
    
    # Recent messages
    recent_messages = Messages.query.order_by(Messages.timestamp.desc()).limit(10).all()
    
    return render_template('admin-dashboard/index.html', 
                         stats={
                             'total_sessions': total_sessions,
                             'total_messages': total_messages, 
                             'active_sessions': active_sessions,
                             'total_users': total_users
                         },
                         recent_messages=recent_messages)

@app.get('/api/v1/admin/stats')
@login_required
def admin_stats():
    """API endpoint for admin statistics"""
    
    # Message counts by sender
    user_messages = Messages.query.filter_by(sender='user').count()
    bot_messages = Messages.query.filter_by(sender='bot').count()
    
    # Sessions today
    from datetime import datetime, timedelta
    today = datetime.now().date()
    sessions_today = Sessions.query.filter(
        func.date(Sessions.created_at) == today
    ).count()
    
    return jsonify({
        'user_messages': user_messages,
        'bot_messages': bot_messages,
        'sessions_today': sessions_today,
        'total_conversations': Sessions.query.count()
    })
