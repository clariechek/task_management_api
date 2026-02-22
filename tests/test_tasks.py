from datetime import date, timedelta
import pytest


class TestCreateTask:
    """Tests for POST /tasks endpoint."""

    def test_create_task_success(self, client):
        """Test successful task creation."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        response = client.post("/tasks", json={
            "title": "Test Task",
            "description": "Test description",
            "priority": 3,
            "due_date": future_date,
            "tags": ["work", "urgent"]
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["priority"] == 3
        assert data["due_date"] == future_date
        assert data["completed"] is False
        assert data["is_deleted"] is False
        assert set(data["tags"]) == {"work", "urgent"} # convert to set for comparison (order doesn't matter)
        assert "id" in data
        assert "created_at" in data

    def test_create_task_missing_title(self, client):
        """Test validation error when title is missing."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post("/tasks", json={
            "priority": 3,
            "due_date": future_date,
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "title" in data["details"]

    def test_create_task_title_too_long(self, client):
        """Test validation error when title exceeds 200 characters."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post("/tasks", json={
            "title": "x" * 201,
            "priority": 3,
            "due_date": future_date,
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "title" in data["details"]

    def test_create_task_invalid_priority_low(self, client):
        """Test validation error when priority is below 1."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post("/tasks", json={
            "title": "Test Task",
            "priority": 0,
            "due_date": future_date,
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "priority" in data["details"]

    def test_create_task_invalid_priority_high(self, client):
        """Test validation error when priority is above 5."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post("/tasks", json={
            "title": "Test Task",
            "priority": 6,
            "due_date": future_date,
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "priority" in data["details"]

    def test_create_task_past_due_date(self, client):
        """Test validation error when due_date is in the past."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = client.post("/tasks", json={
            "title": "Test Task",
            "priority": 3,
            "due_date": past_date,
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "due_date" in data["details"]

