from models import db
from datetime import datetime

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # ✅ Use back_populates - NOT backref (user_comments already defined in User model)
    author = db.relationship('User', back_populates='user_comments', foreign_keys=[author_id])
    post = db.relationship('Post', back_populates='comments', foreign_keys=[post_id])
    
    def __repr__(self):
        return f'<Comment {self.id}>'