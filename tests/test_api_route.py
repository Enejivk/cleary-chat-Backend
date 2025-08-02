from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_user(client: TestClient, db_session: Session):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "created_at" in data

def test_create_user_mismatched_passwords(client: TestClient, db_session: Session):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "differentpassword"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert "passwords do not match" in response.json()["detail"].lower()

def test_create_existing_user(client: TestClient, db_session: Session):
    # Create initial user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    client.post("/users/register", json=user_data)
    
    # Try to create user with same email
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()

def test_login_user(client: TestClient, db_session: Session):
    # First create a user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    client.post("/users/register", json=user_data)
    
    # Try to login
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/users/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient, db_session: Session):
    login_data = {
        "username": "test@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/users/login", data=login_data)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

def test_get_current_user(client: TestClient, db_session: Session):
    
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    client.post("/users/register", json=user_data)
    
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }

    login_response = client.post("/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Test getting user profile
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data

def test_update_profile_unauthorized(client: TestClient, db_session: Session):
    update_data = {
        "name": "Test User",
        "bio": "This is my bio"
    }
    response = client.put("/users/profile", json=update_data)
    assert response.status_code == 401