from models import db

class PostLike(db.Model):
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # ✅ Use back_populates - NOT backref
    user = db.relationship('User', back_populates='user_post_likes', foreign_keys=[user_id])
    post = db.relationship('Post', back_populates='likes', foreign_keys=[post_id])
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)
    
    def __repr__(self):
        return f'<PostLike post_id={self.post_id} user_id={self.user_id}>'