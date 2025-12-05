"""
Basic tests for Face Recognition System
Run with: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Face Recognition System"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


def test_list_faces_empty():
    """Test listing faces when database is empty"""
    response = client.get("/api/list-faces")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "total_faces" in data


def test_face_detection_no_file():
    """Test face detection without uploading a file"""
    response = client.post("/api/face-detection")
    assert response.status_code == 422  # Validation error


def test_save_face_no_name():
    """Test saving face without providing name"""
    response = client.post("/api/save-face")
    assert response.status_code == 422  # Validation error


def test_delete_face_no_params():
    """Test deleting face without parameters"""
    response = client.delete("/api/delete-face")
    assert response.status_code == 400  # Bad request


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
