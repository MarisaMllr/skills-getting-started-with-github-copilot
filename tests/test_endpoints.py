"""
Tests for the FastAPI endpoints of the Mergington High School API.
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_static(self, client: TestClient):
        """Test that root path redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client: TestClient):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_has_required_fields(self, client: TestClient):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"
    
    def test_activity_data_types(self, client: TestClient):
        """Test that activity data has correct types."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            assert all(isinstance(email, str) for email in activity_data["participants"])
    
    def test_activities_have_correct_initial_participants(self, client: TestClient):
        """Test that activities have the correct initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        assert len(data["Programming Class"]["participants"]) == 2
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        
        assert len(data["Gym Class"]["participants"]) == 2
        assert "john@mergington.edu" in data["Gym Class"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_successful_signup(self, client: TestClient, sample_email: str):
        """Test successful signup for an existing activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client: TestClient, sample_email: str):
        """Test that signup actually adds the participant to the activity."""
        # Sign up
        client.post(
            "/activities/Programming Class/signup",
            params={"email": sample_email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities_data = response.json()
        assert sample_email in activities_data["Programming Class"]["participants"]
        assert len(activities_data["Programming Class"]["participants"]) == 3
    
    def test_signup_for_nonexistent_activity(self, client: TestClient, sample_email: str):
        """Test signup fails for nonexistent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_with_duplicate_email(self, client: TestClient):
        """Test that duplicate emails can be added (no validation against duplicates)."""
        existing_email = "michael@mergington.edu"
        
        # Sign up with an email that already exists
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": existing_email}
        )
        assert response.status_code == 200
        
        # Verify email was added again (current behavior allows duplicates)
        response = client.get("/activities")
        activities_data = response.json()
        participants = activities_data["Chess Club"]["participants"]
        assert participants.count(existing_email) == 2  # Same email appears twice (original + signup)
    
    def test_signup_different_activities(self, client: TestClient, sample_email: str):
        """Test signing up for multiple different activities."""
        # Sign up for two activities
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        response2 = client.post(
            "/activities/Gym Class/signup",
            params={"email": sample_email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify signup in both activities
        response = client.get("/activities")
        activities_data = response.json()
        assert sample_email in activities_data["Chess Club"]["participants"]
        assert sample_email in activities_data["Gym Class"]["participants"]
    
    def test_signup_preserves_other_participants(self, client: TestClient, sample_email: str):
        """Test that signup doesn't remove existing participants."""
        # Get initial state
        response = client.get("/activities")
        initial_programming_participants = response.json()["Programming Class"]["participants"].copy()
        
        # Sign up for a different activity
        client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        
        # Verify other activity participants unchanged
        response = client.get("/activities")
        final_programming_participants = response.json()["Programming Class"]["participants"]
        assert initial_programming_participants == final_programming_participants


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_activity_name_with_spaces(self, client: TestClient, sample_email: str):
        """Test that activity names with spaces work correctly."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
    
    def test_empty_email_parameter(self, client: TestClient):
        """Test signup with empty email parameter."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        assert response.status_code == 200
    
    def test_case_sensitive_activity_name(self, client: TestClient, sample_email: str):
        """Test that activity names are case-sensitive."""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": sample_email}
        )
        assert response.status_code == 404
