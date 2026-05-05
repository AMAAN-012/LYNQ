from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from models.user import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        usertag = request.form.get('usertag', '').strip()
        role = request.form.get('role', 'student')
        
        # Validate inputs
        if not email or not full_name or not password or not usertag:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('auth.register'))
        
        # Validate email format based on role
        if role == 'recruiter':
            # Recruiters MUST use @lynqplat.com email
            if not email.endswith('@lynqplat.com'):
                flash('Recruiters must register with a @lynqplat.com email address', 'error')
                return redirect(url_for('auth.register'))
        else:
            # Students can use any valid email
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                flash('Please enter a valid email address', 'error')
                return redirect(url_for('auth.register'))
        
        # Check if user exists
        existing_user = User.query.filter(
            (User.email == email) | (User.usertag == usertag)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                flash('Email already exists', 'error')
            else:
                flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
        
        # Validate username (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]{3,}$', usertag):
            flash('Username must be at least 3 characters (letters, numbers, underscore only)', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            email=email,
            full_name=full_name,
            usertag=usertag,
            is_admin=(role == 'recruiter')  # Recruiter = Admin
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Fetch user from database
        user = User.query.filter_by(email=email).first()
        
        # Verify password
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['username'] = user.usertag
            session['full_name'] = user.full_name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.home'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))