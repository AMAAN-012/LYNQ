from models import db
from datetime import datetime
import time
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    usertag = db.Column(db.String(50), unique=True, nullable=False)
    bio = db.Column(db.Text)
    age = db.Column(db.Integer)
    company_name = db.Column(db.String(120))
    cgpa = db.Column(db.Float)
    is_admin = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(255), default='default_profile.png')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # ✅ All use back_populates
    user_posts = db.relationship('Post', back_populates='author', foreign_keys='Post.author_id', cascade='all, delete-orphan')
    user_comments = db.relationship('Comment', back_populates='author', foreign_keys='Comment.author_id', cascade='all, delete-orphan')
    user_post_likes = db.relationship('PostLike', back_populates='user', foreign_keys='PostLike.user_id', cascade='all, delete-orphan')
    user_skills = db.relationship('Skill', back_populates='user', foreign_keys='Skill.user_id', cascade='all, delete-orphan')
    user_applications = db.relationship('Application', back_populates='user', foreign_keys='Application.user_id', cascade='all, delete-orphan')
    company_jobs = db.relationship('Job', back_populates='company', foreign_keys='Job.company_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_initials(self):
        """Get user initials from full name"""
        names = self.full_name.split()
        if len(names) >= 2:
            return (names[0][0] + names[-1][0]).upper()
        elif len(names) == 1:
            return names[0][0].upper()
        return "U"
    
    def get_profile_picture(self):
        """Get profile picture URL with cache busting"""
        if self.profile_picture and self.profile_picture != 'default_profile.png':
            cache_bust = int(time.time())
            return f'/static/uploads/profiles/{self.profile_picture}?t={cache_bust}'
        return f'https://ui-avatars.com/api/?name={self.full_name.replace(" ", "+")}&background=random'
    
    def get_stats(self):
        """Return a dict of stats for the user's profile page - FIXED with correct keys and conditional logic"""
        # FIX: Changed keys to match template expectations (num_* and total_* formats)
        stats = {
            'num_skills': len(self.user_skills),
            'num_posts': len(self.user_posts),
            'num_comments': len(self.user_comments),
        }
        
        # Add role-specific stats
        if self.is_admin:
            # For admins: show jobs created and applications received
            stats['total_jobs_created'] = len(self.company_jobs)
            
            # Count total applications received for all jobs created by this admin
            from models.job import Job
            from models.application import Application
            total_apps = Application.query.join(Job).filter(Job.company_id == self.id).count()
            stats['applications_received'] = total_apps
        else:
            # For students: show jobs selected (NOT total jobs applied)
            from models.application import Application
            jobs_selected = Application.query.filter_by(user_id=self.id, status='accepted').count()
            stats['jobs_selected'] = jobs_selected
        
        return stats
    
    def __repr__(self):
        return f'<User {self.email}>'