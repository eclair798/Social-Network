from .database import db
from datetime import datetime
import uuid

class Post(db.Model):
    __tablename__ = 'posts'

    post_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)



class Comment(db.Model):
    tablename = 'comments'

    comment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.String(36), db.ForeignKey('posts.post_id'), nullable=False)
    user_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parent_comment_id = db.Column(db.String(36), nullable=True)  # если нужен вложенный ответ

class Like(db.Model):
    tablename = 'likes'

    like_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.String(36), db.ForeignKey('posts.post_id'), nullable=False)
    user_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
