"""
Tests for Mergington High School Activities API
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that all activities are returned"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all three activities are returned
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """Test that activities include all required details"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        
        # Check that all required fields are present
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_shows_current_participants(self, client, reset_activities):
        """Test that activities show current participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_success(self, client, reset_activities):
        """Test that a new student can sign up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newtesting@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newtesting@mergington.edu" in data["message"]
    
    def test_signup_adds_student_to_participants(self, client, reset_activities):
        """Test that signup actually adds the student to participants"""
        # Sign up new student
        client.post("/activities/Programming Class/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        
        assert "newstudent@mergington.edu" in activities["Programming Class"]["participants"]
    
    def test_signup_fail_activity_not_found(self, client, reset_activities):
        """Test that signup fails if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Class/signup?email=newtesting@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_fail_duplicate_registration(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]
    
    def test_signup_multiple_activities_allowed(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups were recorded
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_success(self, client, reset_activities):
        """Test that an existing participant can be unregistered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Unregister participant
        client.post("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 1
    
    def test_unregister_fail_activity_not_found(self, client, reset_activities):
        """Test that unregister fails if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Class/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_fail_student_not_registered(self, client, reset_activities):
        """Test that unregister fails if student is not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_then_signup_again_allowed(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        email = "unstable@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Unregister
        client.post(f"/activities/Gym Class/unregister?email={email}")
        
        # Sign up again - should succeed
        response = client.post(f"/activities/Gym Class/signup?email={email}")
        assert response.status_code == 200


class TestIntegration:
    """Integration tests for signup/unregister workflows"""
    
    def test_full_signup_workflow(self, client, reset_activities):
        """Test a complete signup workflow"""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Before signup
        response = client.get("/activities")
        activities_before = response.json()
        count_before = len(activities_before[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # After signup
        response = client.get("/activities")
        activities_after = response.json()
        count_after = len(activities_after[activity]["participants"])
        
        assert count_after == count_before + 1
        assert email in activities_after[activity]["participants"]
    
    def test_full_unregister_workflow(self, client, reset_activities):
        """Test a complete unregister workflow"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Before unregister
        response = client.get("/activities")
        activities_before = response.json()
        count_before = len(activities_before[activity]["participants"])
        assert email in activities_before[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # After unregister
        response = client.get("/activities")
        activities_after = response.json()
        count_after = len(activities_after[activity]["participants"])
        
        assert count_after == count_before - 1
        assert email not in activities_after[activity]["participants"]
