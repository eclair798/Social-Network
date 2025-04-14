import pytest
from app import create_app, db
from flask_jwt_extended import create_access_token
from app.models import User, UserProfile
from werkzeug.security import generate_password_hash
import uuid

@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        
        test_user = User(
            user_id=str(uuid.uuid4()),
            username="testuser",
            email="testuser@example.com",
            password_hash=generate_password_hash("testpass")
        )
        db.session.add(test_user)

        test_profile = UserProfile(
            profile_id=str(uuid.uuid4()),
            user_id=test_user.user_id,
            first_name="John",
            last_name="Doe"
        )
        db.session.add(test_profile)

        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def token(app):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        access_token = create_access_token(identity=user.user_id)
        return access_token

def test_register(client):
    response = client.post('/user/register', json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpass"
    })
    assert response.status_code == 201
    assert response.get_json()["username"] == "newuser"

def test_login(client):
    response = client.post('/user/login', json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "user_token" in response.get_json()

def test_update_profile(client, token):
    response = client.put('/user/update_profile', json={
        "first_name": "Jane",
        "last_name": "Updated"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.get_json()["msg"] == "Profile updated successfully"

def test_read_profile(client, token):
    response = client.get('/user/read_profile', headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
