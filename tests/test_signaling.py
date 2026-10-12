import json


def test_websocket_signaling_flow(client):
    meeting_id = "842-1920-3341"

    # Client A connects
    with client.websocket_connect(f"/ws/meetings/{meeting_id}/client-a?display_name=ClientA") as ws_a:
        init_a = ws_a.receive_json()
        assert init_a["type"] == "room-state"
        assert init_a["clientId"] == "client-a"
        assert init_a["peers"] == []

        # Client B connects
        with client.websocket_connect(f"/ws/meetings/{meeting_id}/client-b?display_name=ClientB") as ws_b:
            init_b = ws_b.receive_json()
            assert init_b["type"] == "room-state"
            assert init_b["clientId"] == "client-b"
            assert len(init_b["peers"]) == 1
            assert init_b["peers"][0]["clientId"] == "client-a"

            # Client A receives peer-joined
            joined_msg = ws_a.receive_json()
            assert joined_msg["type"] == "peer-joined"
            assert joined_msg["clientId"] == "client-b"

            # Chat message test
            ws_a.send_json({
                "type": "chat-message",
                "text": "Hello from A!"
            })

            # Both A and B receive the chat message
            chat_a = ws_a.receive_json()
            assert chat_a["type"] == "chat-message"
            assert chat_a["text"] == "Hello from A!"

            chat_b = ws_b.receive_json()
            assert chat_b["type"] == "chat-message"
            assert chat_b["text"] == "Hello from A!"

            # Reaction test
            ws_b.send_json({
                "type": "reaction",
                "emoji": "👍"
            })
            react_a = ws_a.receive_json()
            assert react_a["type"] == "reaction"
            assert react_a["emoji"] == "👍"

            react_b = ws_b.receive_json()
            assert react_b["type"] == "reaction"
            assert react_b["emoji"] == "👍"

            # Media state test
            ws_a.send_json({
                "type": "media-state",
                "audio": False,
                "video": False
            })
            media_b = ws_b.receive_json()
            assert media_b["type"] == "media-state"
            assert media_b["audio"] is False

            # Mute all host control
            ws_a.send_json({
                "type": "mute-all"
            })
            mute_all_b = ws_b.receive_json()
            assert mute_all_b["type"] == "mute-all"
