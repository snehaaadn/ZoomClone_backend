def test_update_participant_audio_and_video(client):
    # Create instant meeting
    res = client.post("/api/meetings/instant", json={"title": "Participant Test Sync"})
    meeting_id = res.json()["meeting_id"]

    # Join as attendee
    join_res = client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "Charlie Puth",
        "client_id": "charlie-client-1"
    })
    assert join_res.status_code == 200
    participant_id = join_res.json()["id"]

    # Mute participant audio
    patch_res = client.patch(f"/api/participants/{participant_id}", json={
        "is_muted": True,
        "is_video_on": False
    })
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["is_muted"] is True
    assert updated["is_video_on"] is False


def test_remove_participant_by_host(client):
    res = client.post("/api/meetings/instant", json={"title": "Remove Test"})
    meeting_id = res.json()["meeting_id"]

    join_res = client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "Disruptive User",
        "client_id": "user-remove-99"
    })
    participant_id = join_res.json()["id"]

    del_res = client.delete(f"/api/participants/{participant_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Participant removed from meeting"


def test_list_meeting_participants(client):
    res = client.post("/api/meetings/instant", json={"title": "List Attendees Test"})
    meeting_id = res.json()["meeting_id"]

    client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "User Alpha",
        "client_id": "alpha-1"
    })
    client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "User Beta",
        "client_id": "beta-2"
    })

    list_res = client.get(f"/api/meetings/{meeting_id}/participants")
    assert list_res.status_code == 200
    participants = list_res.json()
    names = [p["display_name"] for p in participants]
    assert "User Alpha" in names
    assert "User Beta" in names


def test_participant_not_found(client):
    res = client.patch("/api/participants/99999", json={"is_muted": True})
    assert res.status_code == 404

    del_res = client.delete("/api/participants/99999")
    assert del_res.status_code == 404


def test_guest_flow_with_unique_participant_identities(client):
    # 1. Sneha creates meeting
    create_res = client.post("/api/meetings/instant", json={
        "title": "Team Standup",
        "host_display_name": "Sneha Debnath"
    })
    assert create_res.status_code == 201
    meeting_data = create_res.json()
    meeting_id = meeting_data["meeting_id"]
    assert meeting_data["host_display_name"] == "Sneha Debnath"

    # Sneha joins as host
    host_join = client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "Sneha Debnath",
        "client_id": "sneha-client-host-1",
        "is_host": True
    })
    assert host_join.status_code == 200
    host_part = host_join.json()
    assert host_part["is_host"] is True
    assert host_part["display_name"] == "Sneha Debnath"

    # 2. Friend Rahul joins as guest
    rahul_join = client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "Rahul",
        "client_id": "rahul-guest-client-2",
        "is_host": False
    })
    assert rahul_join.status_code == 200
    rahul_part = rahul_join.json()
    assert rahul_part["is_host"] is False
    assert rahul_part["display_name"] == "Rahul"
    assert rahul_part["id"] != host_part["id"]

    # 3. Friend Priya joins as guest
    priya_join = client.post(f"/api/meetings/{meeting_id}/join", json={
        "display_name": "Priya",
        "client_id": "priya-guest-client-3",
        "is_host": False
    })
    assert priya_join.status_code == 200
    priya_part = priya_join.json()
    assert priya_part["is_host"] is False
    assert priya_part["display_name"] == "Priya"
    assert priya_part["id"] != rahul_part["id"]
    assert priya_part["id"] != host_part["id"]

    # 4. Verify all three participants appear separately
    part_list_res = client.get(f"/api/meetings/{meeting_id}/participants")
    assert part_list_res.status_code == 200
    participants = part_list_res.json()
    assert len(participants) == 3

    display_names = {p["display_name"]: p for p in participants}
    assert "Sneha Debnath" in display_names
    assert display_names["Sneha Debnath"]["is_host"] is True
    assert "Rahul" in display_names
    assert display_names["Rahul"]["is_host"] is False
    assert "Priya" in display_names
    assert display_names["Priya"]["is_host"] is False

    # 5. Rahul leaves meeting: only Rahul's status updates to 'left', meeting remains active
    leave_res = client.post(f"/api/meetings/{meeting_id}/leave?client_id=rahul-guest-client-2")
    assert leave_res.status_code == 200

    # Verify meeting is still active
    meeting_check = client.get(f"/api/meetings/{meeting_id}")
    assert meeting_check.status_code == 200
    assert meeting_check.json()["status"] == "active"

    # Verify Rahul is excluded from active participants (active_only=True by default)
    active_parts = client.get(f"/api/meetings/{meeting_id}/participants").json()
    active_names = [p["display_name"] for p in active_parts]
    assert "Rahul" not in active_names
    assert "Sneha Debnath" in active_names
    assert "Priya" in active_names
    assert len(active_parts) == 2

    # Verify Rahul is marked 'left' in the complete participants history (active_only=False)
    all_parts = client.get(f"/api/meetings/{meeting_id}/participants?active_only=false").json()
    part_status = {p["display_name"]: p["status"] for p in all_parts}
    assert part_status["Rahul"] == "left"
    assert part_status["Sneha Debnath"] == "in_meeting"
    assert part_status["Priya"] == "in_meeting"
