from .database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    profile_id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.user_id'))
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
