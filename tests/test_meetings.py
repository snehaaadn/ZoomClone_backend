from datetime import datetime, timedelta, timezone


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_upcoming_meetings(client):
    response = client.get("/api/meetings/upcoming")
    assert response.status_code == 200
    meetings = response.json()
    assert isinstance(meetings, list)
    assert len(meetings) >= 3
    # Check that sample meetings are present
    titles = [m["title"] for m in meetings]
    assert any("Weekly Engineering Sync" in t for t in titles)


def test_list_recent_meetings(client):
    response = client.get("/api/meetings/recent")
    assert response.status_code == 200
    meetings = response.json()
    assert isinstance(meetings, list)
    assert len(meetings) >= 2


def test_create_instant_meeting(client):
    payload = {
        "title": "Ad-hoc Review Meeting",
        "host_display_name": "Test Host"
    }
    response = client.post("/api/meetings/instant", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Ad-hoc Review Meeting"
    assert data["host_display_name"] == "Test Host"
    assert data["status"] == "active"
    assert data["is_instant"] is True
    assert "-" in data["meeting_id"]
    assert "invite_token" in data
    assert "invite_url" in data


def test_schedule_meeting(client):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "Quarterly Sprint Planning",
        "description": "Planning goals and roadmap for Q3.",
        "start_time": future_time,
        "duration": 60,
        "host_display_name": "Test Host"
    }
    response = client.post("/api/meetings/schedule", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Quarterly Sprint Planning"
    assert data["duration"] == 60
    assert data["status"] == "scheduled"
    assert data["is_instant"] is False


def test_schedule_meeting_validation_error(client):
    # Empty title should fail Pydantic validation
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "   ",
        "start_time": future_time,
        "duration": 30
    }
    response = client.post("/api/meetings/schedule", json=payload)
    assert response.status_code == 422


def test_get_meeting_details_and_not_found(client):
    # Retrieve upcoming meetings to get an ID
    res = client.get("/api/meetings/upcoming")
    sample_id = res.json()[0]["meeting_id"]

    # Valid get
    response = client.get(f"/api/meetings/{sample_id}")
    assert response.status_code == 200
    assert response.json()["meeting_id"] == sample_id

    # Invalid get
    response_404 = client.get("/api/meetings/non-existent-id-999")
    assert response_404.status_code == 404


def test_validate_meeting(client):
    res = client.get("/api/meetings/upcoming")
    sample_id = res.json()[0]["meeting_id"]

    # Validate valid meeting
    val_res = client.get(f"/api/meetings/{sample_id}/validate")
    assert val_res.status_code == 200
    assert val_res.json()["exists"] is True
    assert val_res.json()["is_valid"] is True

    # Validate non-existent meeting
    val_404 = client.get("/api/meetings/000-000-000/validate")
    assert val_404.status_code == 200
    assert val_404.json()["exists"] is False
    assert val_404.json()["is_valid"] is False


def test_join_and_leave_meeting(client):
    # Create an instant meeting first
    create_res = client.post("/api/meetings/instant", json={"title": "Join Test Meeting"})
    meeting_id = create_res.json()["meeting_id"]

    # Join meeting
    join_payload = {
        "display_name": "Bob Dylan",
        "client_id": "bob-client-123"
    }
    join_res = client.post(f"/api/meetings/{meeting_id}/join", json=join_payload)
    assert join_res.status_code == 200
    participant = join_res.json()
    assert participant["display_name"] == "Bob Dylan"
    assert participant["status"] == "in_meeting"

    # Leave meeting
    leave_res = client.post(f"/api/meetings/{meeting_id}/leave?client_id=bob-client-123")
    assert leave_res.status_code == 200


def test_end_meeting_by_host(client):
    create_res = client.post("/api/meetings/instant", json={"title": "Meeting to End"})
    meeting_id = create_res.json()["meeting_id"]

    end_res = client.post(f"/api/meetings/{meeting_id}/end")
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "ended"

    # Validation should now say is_valid = False
    val_res = client.get(f"/api/meetings/{meeting_id}/validate")
    assert val_res.status_code == 200
    assert val_res.json()["exists"] is True
    assert val_res.json()["is_valid"] is False
    assert val_res.json()["status"] == "ended"


def test_cancel_scheduled_meeting(client):
    future_time = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sched_res = client.post("/api/meetings/schedule", json={
        "title": "Meeting to Cancel",
        "start_time": future_time,
        "duration": 30
    })
    meeting_id = sched_res.json()["meeting_id"]

    cancel_res = client.post(f"/api/meetings/{meeting_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
