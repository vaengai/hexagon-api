import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models import HexagonUser
from app.user_service import get_or_create_local_user

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_clerk_user():
    user = MagicMock()
    user.id = "clerk_user_123"
    user.email_addresses = [MagicMock(email_address="test@example.com")]
    user.first_name = "Test"
    user.last_name = "User"
    user.metadata = {"source": "clerk"}  # ✅ Explicitly a dict
    return user

@patch("app.user_service.clerk")
def test_get_or_create_local_user_existing(mock_clerk, mock_db_session):
    existing_user = HexagonUser(
        id="clerk_user_123",
        email="test@example.com",
        full_name="Test User",
        clerk_metadata={"source": "clerk"}
    )
    mock_db_session.query().filter_by().first.return_value = existing_user

    user = get_or_create_local_user("clerk_user_123", db=mock_db_session)

    assert user == existing_user
    mock_clerk.users.get_user.assert_not_called()

@patch("app.user_service.clerk")
def test_get_or_create_local_user_new(mock_clerk, mock_db_session, mock_clerk_user):
    mock_db_session.query().filter_by().first.return_value = None
    mock_clerk.users.get_user.return_value = mock_clerk_user

    user = get_or_create_local_user("clerk_user_123", db=mock_db_session)

    assert user.id == "clerk_user_123"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.clerk_metadata == {"source": "clerk"}
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()