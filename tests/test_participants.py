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
