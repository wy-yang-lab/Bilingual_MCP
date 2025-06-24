"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "MCP-UI-Terminology Checker with LLM Integration"
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_context_request_valid(self):
        """Test valid context request."""
        headers = {"Authorization": "Bearer TEST_TOKEN"}
        payload = {
            "text": "Please login to continue",
            "lang": "en"
        }
        
        response = client.post("/context-request", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "issues" in data
        assert data["text"] == payload["text"]
        assert data["lang"] == payload["lang"]
        assert len(data["issues"]) == 1
        assert data["issues"][0]["original"] == "login"
    
    def test_context_request_unauthorized(self):
        """Test context request without authorization."""
        payload = {
            "text": "Please login to continue",
            "lang": "en"
        }
        
        response = client.post("/context-request", json=payload)
        assert response.status_code == 401
    
    def test_context_request_invalid_token(self):
        """Test context request with invalid token."""
        headers = {"Authorization": "Bearer INVALID_TOKEN"}
        payload = {
            "text": "Please login to continue",
            "lang": "en"
        }
        
        response = client.post("/context-request", json=payload, headers=headers)
        assert response.status_code == 401
    
    def test_context_request_invalid_language(self):
        """Test context request with invalid language."""
        headers = {"Authorization": "Bearer TEST_TOKEN"}
        payload = {
            "text": "Bonjour le monde",
            "lang": "fr"  # Unsupported language
        }
        
        response = client.post("/context-request", json=payload, headers=headers)
        assert response.status_code == 400
    
    def test_list_resources(self):
        """Test the resources listing endpoint."""
        headers = {"Authorization": "Bearer TEST_TOKEN"}
        
        response = client.get("/resources", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "resources" in data
        assert len(data["resources"]) == 3
        
        # Check that EN, JP, and LLM resources are listed
        uris = [resource["uri"] for resource in data["resources"]]
        assert "terminology://en" in uris
        assert "terminology://jp" in uris
        assert "llm://analysis" in uris
    
    def test_list_resources_unauthorized(self):
        """Test resources endpoint without authorization."""
        response = client.get("/resources")
        assert response.status_code == 401 