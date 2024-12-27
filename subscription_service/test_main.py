from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app, get_current_user

from database import User, Journal
from main import app, pwd_context

client = TestClient(app)


@pytest.fixture(scope="module")
def mock_db():
    mock_session = MagicMock(spec=Session)
    with patch('main.database.SessionLocal', return_value=mock_session):
        yield mock_session


def test_login_success(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = User(id=1, email="test@test.com",
                                                                             hashed_password="hashed")
    mock_db.query.return_value.filter.return_value.first.return_value.hashed_password = "hashed"
    pwd_context.verify = lambda a, b: True
    response = client.post("/token", data={"username": "test@test.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_all_journals(mock_db):
    mock_db.query.return_value.all.return_value = [{"id": 1, "name": "test", "user_id": 1}]
    response = client.get("/journals")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "test", "user_id": 1}]


def test_get_user_journals(mock_db):
    app.dependency_overrides[get_current_user] = lambda: 1
    mock_db.query.return_value.filter.return_value.all.return_value = [{"id": 1, "name": "test", "user_id": 1}]
    response = client.get("/journals/user")
    print(response.json())
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "test", "user_id": 1}]


def test_search_journals(mock_db):
    mock_db.query.return_value.filter.return_value.all.return_value = [{"id": 1, "name": "test", "user_id": 1}]
    response = client.get("/journals/search?query=test")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "test", "user_id": 1}]


def test_delete_journal(mock_db):
    app.dependency_overrides[get_current_user] = lambda: 1
    mock_db.query.return_value.filter.return_value.first.return_value = Journal(id=1, name="test", user_id=1)
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    response = client.delete("/journals/1")
    assert response.status_code == 200

