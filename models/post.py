from models import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    likes_count = db.Column(db.Integer, default=0)
    
    # ✅ Use back_populates - NOT backref
    author = db.relationship('User', back_populates='user_posts', foreign_keys=[author_id])
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    likes = db.relationship('PostLike', back_populates='post', cascade='all, delete-orphan')
    
    def has_user_liked(self, user_id):
        from models.post_like import PostLike
        return PostLike.query.filter_by(post_id=self.id, user_id=user_id).first() is not None
    
    def __repr__(self):
        return f'<Post {self.id}>'