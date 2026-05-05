from models import db
from datetime import datetime

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    linkedin_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    resume_filename = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    review_notes = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.now)
    reviewed_at = db.Column(db.DateTime)
    
    # ✅ Use back_populates - NOT backref
    user = db.relationship('User', back_populates='user_applications', foreign_keys=[user_id])
    job = db.relationship('Job', back_populates='job_applications', foreign_keys=[job_id])
    
    def __repr__(self):
        return f'<Application {self.id}>'