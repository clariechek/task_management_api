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

class TestGetTasks:
    """Tests for GET /tasks endpoint."""

    def test_get_tasks_empty(self, client):
        """Test getting tasks when none exist."""
        response = client.get("/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tasks"] == []

    def test_get_tasks_pagination(self, client):
        """Test pagination with limit and offset."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        
        for i in range(5):
            client.post("/tasks", json={
                "title": f"Task {i}",
                "priority": 3,
                "due_date": future_date,
            })
        
        response = client.get("/tasks", params={"limit": 2, "offset": 0})
        data = response.json()
        assert data["total"] == 5
        assert len(data["tasks"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        
        response = client.get("/tasks", params={"limit": 2, "offset": 2})
        data = response.json()
        assert data["total"] == 5
        assert len(data["tasks"]) == 2
        assert data["offset"] == 2

    def test_get_tasks_filter_by_priority(self, client):
        """Test filtering tasks by priority."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        
        client.post("/tasks", json={"title": "Low Priority", "priority": 1, "due_date": future_date})
        client.post("/tasks", json={"title": "High Priority", "priority": 5, "due_date": future_date})
        client.post("/tasks", json={"title": "Medium Priority", "priority": 3, "due_date": future_date})
        
        response = client.get("/tasks", params={"priority": 5})
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "High Priority"

    def test_get_tasks_filter_by_completed(self, client):
        """Test filtering tasks by completion status."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        
        response = client.post("/tasks", json={"title": "Task 1", "priority": 3, "due_date": future_date})
        task_id = response.json()["id"]
        client.post("/tasks", json={"title": "Task 2", "priority": 3, "due_date": future_date})
        
        client.patch(f"/tasks/{task_id}", json={"completed": True})
        
        response = client.get("/tasks", params={"completed": True})
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["completed"] is True
        
        response = client.get("/tasks", params={"completed": False})
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["completed"] is False

    def test_get_tasks_filter_by_tags(self, client):
        """Test filtering tasks by tags (any match)."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        
        client.post("/tasks", json={
            "title": "Work Task",
            "priority": 3,
            "due_date": future_date,
            "tags": ["work"]
        })
        client.post("/tasks", json={
            "title": "Personal Task",
            "priority": 3,
            "due_date": future_date,
            "tags": ["personal"]
        })
        client.post("/tasks", json={
            "title": "Work Urgent Task",
            "priority": 5,
            "due_date": future_date,
            "tags": ["work", "urgent"]
        })
        
        response = client.get("/tasks", params={"tags": "work"})
        data = response.json()
        assert data["total"] == 2
        
        response = client.get("/tasks", params={"tags": "work,urgent"})
        data = response.json()
        assert data["total"] == 2
        
        response = client.get("/tasks", params={"tags": "personal"})
        data = response.json()
        assert data["total"] == 1

class TestUpdateTask:
    """Tests for PATCH /tasks/{id} endpoint."""

    def test_update_task_single_field(self, client):
        """Test updating a single field."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_response = client.post("/tasks", json={
            "title": "Original Title",
            "priority": 3,
            "due_date": future_date,
        })
        task_id = create_response.json()["id"]
        
        response = client.patch(f"/tasks/{task_id}", json={"title": "Updated Title"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == 3

    def test_update_task_multiple_fields(self, client):
        """Test updating multiple fields at once."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        new_date = (date.today() + timedelta(days=14)).isoformat()
        create_response = client.post("/tasks", json={
            "title": "Original",
            "priority": 1,
            "due_date": future_date,
        })
        task_id = create_response.json()["id"]
        
        response = client.patch(f"/tasks/{task_id}", json={
            "title": "Updated",
            "priority": 5,
            "due_date": new_date,
            "completed": True,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == 5
        assert data["due_date"] == new_date
        assert data["completed"] is True

    def test_update_task_tags(self, client):
        """Test updating task tags."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_response = client.post("/tasks", json={
            "title": "Task",
            "priority": 3,
            "due_date": future_date,
            "tags": ["old", "tags"]
        })
        task_id = create_response.json()["id"]
        
        response = client.patch(f"/tasks/{task_id}", json={"tags": ["new", "updated"]})
        
        assert response.status_code == 200
        data = response.json()
        assert set(data["tags"]) == {"new", "updated"}

    def test_update_task_not_found(self, client):
        """Test 404 when updating non-existent task."""
        response = client.patch("/tasks/99999", json={"title": "Updated"})
        
        assert response.status_code == 404

    def test_update_task_invalid_priority(self, client):
        """Test validation error on invalid priority update."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_response = client.post("/tasks", json={
            "title": "Task",
            "priority": 3,
            "due_date": future_date,
        })
        task_id = create_response.json()["id"]
        
        response = client.patch(f"/tasks/{task_id}", json={"priority": 10})
        
        assert response.status_code == 422

