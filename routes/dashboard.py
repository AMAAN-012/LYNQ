from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.user import User
from models.post import Post

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def check_user_session():
    if 'user_id' not in session:
        return None
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Your session has expired. Please login again.', 'error')
        return None
    
    return user

@dashboard_bp.route('/')
def home():
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get recent posts only (jobs don't have images anyway)
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    
    activities = []
    for post in recent_posts:
        activities.append({
            'type': 'post',
            'user': post.author,
            'content': post.content,
            'image': f'/static/uploads/posts/{post.image_filename}' if post.image_filename else None,
            'created_at': post.created_at
        })
    
    return render_template('dashboard/home.html', 
                         user=user, 
                         recent_activities=activities)