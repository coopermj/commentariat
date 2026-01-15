"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(sample_commentary):
    """Create test client with sample data."""
    return TestClient(app)


def test_healthz(client):
    """Health endpoint should return ok."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_books(client):
    """Books endpoint should return all books."""
    response = client.get("/books")
    assert response.status_code == 200
    books = response.json()["books"]
    assert len(books) == 66


def test_list_commentaries(client):
    """Should list all commentaries."""
    response = client.get("/commentaries")
    assert response.status_code == 200
    data = response.json()
    assert len(data["commentaries"]) == 1


def test_get_commentary(client):
    """Should get commentary by slug."""
    response = client.get("/commentaries/test-comm")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Commentary"
    assert "id" not in data  # Internal ID should be stripped


def test_get_commentary_not_found(client):
    """Should return 404 for unknown commentary."""
    response = client.get("/commentaries/nonexistent")
    assert response.status_code == 404


def test_get_chapter(client):
    """Should get chapter entries."""
    response = client.get("/commentaries/test-comm/genesis/1")
    assert response.status_code == 200
    data = response.json()
    assert data["book"] == "Genesis"
    assert data["chapter"] == 1
    assert data["count"] == 2


def test_get_chapter_normalizes_book(client):
    """Should accept book aliases."""
    response = client.get("/commentaries/test-comm/gen/1")
    assert response.status_code == 200
    assert response.json()["book"] == "Genesis"


def test_get_chapter_invalid_book(client):
    """Should return 400 for invalid book name."""
    response = client.get("/commentaries/test-comm/notabook/1")
    assert response.status_code == 400
    assert "Unknown book" in response.json()["detail"]


def test_get_chapter_invalid_chapter(client):
    """Should return 400 for non-positive chapter."""
    response = client.get("/commentaries/test-comm/genesis/0")
    assert response.status_code == 400
    assert "positive" in response.json()["detail"]


def test_get_verse(client):
    """Should get verse entries."""
    response = client.get("/commentaries/test-comm/genesis/1/1")
    assert response.status_code == 200
    data = response.json()
    assert data["verse"] == 1
    assert data["count"] == 1


def test_get_verse_invalid(client):
    """Should return 400 for non-positive verse."""
    response = client.get("/commentaries/test-comm/genesis/1/0")
    assert response.status_code == 400
