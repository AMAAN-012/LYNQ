from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models AFTER db is created
from models.user import User
from models.post import Post
from models.comment import Comment
from models.post_like import PostLike
from models.skill import Skill
from models.job import Job
from models.application import Application

__all__ = ['db', 'User', 'Post', 'Comment', 'PostLike', 'Skill', 'Job', 'Application']