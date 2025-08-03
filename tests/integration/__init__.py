import pytest
from fastapi.testclient import TestClient
from app.main import app, get_db, get_current_user, get_or_create_local_user
from types import SimpleNamespace
from unittest.mock import MagicMock

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: {"sub": "clerk_user_id"}
    app.dependency_overrides[get_or_create_local_user] = lambda clerk_user_id, db: SimpleNamespace(
        id="1", email="user@example.com", full_name="Test User"
    )
    yield
    app.dependency_overrides = {}

def test_get_profile_endpoint():
    response = client.get("/profile")
    assert response.status_code == 200
    assert response.json()["local_user"] == {
        "id": "1",
        "email": "user@example.com",
        "full_name": "Test User"
    }
