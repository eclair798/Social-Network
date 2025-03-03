from flask import Blueprint, request, jsonify
from .models import User, UserProfile
from .database import db
from .schemas import user_schema
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bp = Blueprint('routes', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    required_fields = ['username', 'email', 'password']
    
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing fields in request"}), 400
    

    u_id = str(uuid.uuid4())

    new_user = User(
        user_id=u_id,
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )

    new_user_profile = UserProfile(
        profile_id = str(uuid.uuid4()),
        user_id=u_id
    )

    db.session.add(new_user)
    db.session.add(new_user_profile)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to register", "error": str(e)}), 500
    
    return user_schema.jsonify(new_user), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    required_fields = ['username', 'password']
    
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing fields in request"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.user_id)
        return {"msg": "Login is successful", "token": access_token}, 200
    return jsonify({"msg": "Invalid credentials"}), 401

@bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    user = User.query.filter_by(user_id=current_user_id).first()
    user_profile = UserProfile.query.filter_by(user_id=current_user_id).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    if 'first_name' in data:
        user_profile.first_name = data['first_name']
    if 'last_name' in data:
        user_profile.last_name = data['last_name']
    if 'date_of_birth' in data:
        user_profile.date_of_birth = data['date_of_birth']
    if 'phone' in data:
        user_profile.phone = data['phone']
    if 'bio' in data:
        user_profile.bio = data['bio']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to update profile", "error": str(e)}), 500

    return jsonify({"msg": "Profile updated successfully"}), 200


@bp.route('/read_profile', methods=['GET'])
@jwt_required()
def read_profile():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user_id).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    user_profile = UserProfile.query.filter_by(user_id=current_user_id).first()

    if not user_profile:
        return jsonify({"msg": "Profile not found"}), 404

    profile_data = {
        "username": user.username,
        "email": user.email,
        "first_name": user_profile.first_name,
        "last_name": user_profile.last_name,
        "date_of_birth": user_profile.date_of_birth,
        "phone": user_profile.phone,
        "bio": user_profile.bio
    }

    return jsonify(profile_data), 200
