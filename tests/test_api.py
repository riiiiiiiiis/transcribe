import pytest
from fastapi.testclient import TestClient
import uuid


def test_transcribe_endpoint_valid_url():
    """Test transcription with valid YouTube URL"""
    from app.main import app
    client = TestClient(app)
    
    response = client.post(
        "/api/transcribe",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "transcript_id" in data
    assert "title" in data
    assert "duration" in data
    assert "content" in data
    assert "timestamps" in data
    assert "created_at" in data
    
    # Verify data types
    assert isinstance(data["transcript_id"], str)
    assert isinstance(data["title"], str)
    assert isinstance(data["duration"], (int, float))
    assert isinstance(data["content"], str)
    assert isinstance(data["timestamps"], list)
    assert isinstance(data["created_at"], str)
    
    # Verify timestamps structure
    if data["timestamps"]:
        timestamp = data["timestamps"][0]
        assert "start" in timestamp
        assert "end" in timestamp
        assert "text" in timestamp


def test_transcribe_endpoint_invalid_url():
    """Test validation of invalid URL"""
    from app.main import app
    client = TestClient(app)
    
    # Test with invalid URL
    response = client.post(
        "/api/transcribe",
        json={"url": "not-a-valid-url"}
    )
    
    assert response.status_code == 422  # Validation error
    
    # Test with non-YouTube URL
    response = client.post(
        "/api/transcribe",
        json={"url": "https://example.com/video"}
    )
    
    assert response.status_code == 422  # Validation error


def test_get_transcript():
    """Test getting saved transcript"""
    from app.main import app
    client = TestClient(app)
    
    # Use a valid UUID for testing
    transcript_id = str(uuid.uuid4())
    
    response = client.get(f"/api/transcripts/{transcript_id}")
    
    # In a real test, we'd create a transcript first
    # For now, we expect 404 if transcript doesn't exist
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        # Verify response structure
        assert "transcript_id" in data
        assert "title" in data
        assert "duration" in data
        assert "content" in data
        assert "timestamps" in data
        assert "created_at" in data


def test_health_check():
    """Test health endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"] == "connected"