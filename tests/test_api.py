import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Тест health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_transcription_job():
    """Тест создания job'а с валидным YouTube URL"""
    payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    response = client.post("/api/transcribe", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

def test_create_job_invalid_url():
    """Тест валидации невалидного URL"""
    payload = {"url": "https://invalid-url.com"}
    response = client.post("/api/transcribe", json=payload)
    assert response.status_code == 422

def test_get_pending_jobs():
    """Тест получения pending jobs"""
    response = client.get("/api/jobs/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_mark_job_processing():
    """Тест пометки job'а как processing"""
    # Создать job
    job_response = client.post("/api/transcribe", json={"url": "https://youtube.com/watch?v=test"})
    job_id = job_response.json()["job_id"]
    
    # Пометить как processing
    response = client.put(f"/api/jobs/{job_id}/processing")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

def test_complete_job():
    """Тест завершения job'а с результатом"""
    # Создать job
    job_response = client.post("/api/transcribe", json={"url": "https://youtube.com/watch?v=test"})
    job_id = job_response.json()["job_id"]
    
    # Завершить job
    result = {
        "title": "Test Video",
        "duration": 300,
        "content": "Test transcript content",
        "timestamps": [{"start": 0.0, "end": 5.0, "text": "Test"}]
    }
    response = client.put(f"/api/jobs/{job_id}/complete", json=result)
    assert response.status_code == 200
    assert "transcript_id" in response.json()

def test_fail_job():
    """Тест пометки job'а как failed"""
    job_response = client.post("/api/transcribe", json={"url": "https://youtube.com/watch?v=test"})
    job_id = job_response.json()["job_id"]
    
    response = client.put(f"/api/jobs/{job_id}/fail", json={"error": "Test error"})
    assert response.status_code == 200

def test_get_job_status():
    """Тест получения статуса job'а"""
    job_response = client.post("/api/transcribe", json={"url": "https://youtube.com/watch?v=test"})
    job_id = job_response.json()["job_id"]
    
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "processing", "completed", "failed"]

def test_get_transcript():
    """Тест получения готового транскрипта"""
    # Создать и завершить job
    job_response = client.post("/api/transcribe", json={"url": "https://youtube.com/watch?v=test"})
    job_id = job_response.json()["job_id"]
    
    result = {
        "title": "Test Video",
        "duration": 300,
        "content": "Test transcript",
        "timestamps": [{"start": 0.0, "end": 5.0, "text": "Test"}]
    }
    complete_response = client.put(f"/api/jobs/{job_id}/complete", json=result)
    transcript_id = complete_response.json()["transcript_id"]
    
    # Получить транскрипт
    response = client.get(f"/api/transcripts/{transcript_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["content"] == "Test transcript"