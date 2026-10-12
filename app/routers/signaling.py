import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("signaling")

router = APIRouter(tags=["signaling"])


class ConnectionManager:
    def __init__(self):
        # meeting_id -> {client_id: {"websocket": WebSocket, "display_name": str, "audio": bool, "video": bool, "screen": bool}}
        self.rooms: Dict[str, Dict[str, Any]] = {}

    async def connect(self, meeting_id: str, client_id: str, display_name: str, websocket: WebSocket):
        await websocket.accept()
        if meeting_id not in self.rooms:
            self.rooms[meeting_id] = {}

        self.rooms[meeting_id][client_id] = {
            "websocket": websocket,
            "display_name": display_name,
            "audio": True,
            "video": True,
            "screen": False,
        }
        logger.info(f"Client {client_id} ({display_name}) connected to meeting {meeting_id}")

        # Send existing peers list with their current media states to the newly connected client
        existing_peers = [
            {
                "clientId": cid,
                "displayName": data["display_name"],
                "isMuted": not data.get("audio", True),
                "isVideoOff": not data.get("video", True),
                "isScreenSharing": bool(data.get("screen", False)),
            }
            for cid, data in self.rooms[meeting_id].items()
            if cid != client_id
        ]
        
        await websocket.send_text(json.dumps({
            "type": "room-state",
            "clientId": client_id,
            "peers": existing_peers
        }))

        # Broadcast to all OTHER peers that this client has joined
        await self.broadcast_to_others(meeting_id, client_id, {
            "type": "peer-joined",
            "clientId": client_id,
            "displayName": display_name,
            "isMuted": False,
            "isVideoOff": False,
        })

    def disconnect(self, meeting_id: str, client_id: str):
        if meeting_id in self.rooms and client_id in self.rooms[meeting_id]:
            del self.rooms[meeting_id][client_id]
            logger.info(f"Client {client_id} removed from meeting {meeting_id}")
            if not self.rooms[meeting_id]:
                del self.rooms[meeting_id]

    async def send_to_client(self, meeting_id: str, target_client_id: str, message: dict):
        if meeting_id in self.rooms and target_client_id in self.rooms[meeting_id]:
            ws = self.rooms[meeting_id][target_client_id]["websocket"]
            try:
                await ws.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error sending to {target_client_id}: {e}")

    async def broadcast_to_room(self, meeting_id: str, message: dict):
        if meeting_id not in self.rooms:
            return
        payload = json.dumps(message)
        dead_clients = []
        for cid, data in self.rooms[meeting_id].items():
            try:
                await data["websocket"].send_text(payload)
            except Exception as e:
                logger.warning(f"Broadcast failure to {cid}: {e}")
                dead_clients.append(cid)
        for cid in dead_clients:
            self.disconnect(meeting_id, cid)

    async def broadcast_to_others(self, meeting_id: str, sender_client_id: str, message: dict):
        if meeting_id not in self.rooms:
            return
        payload = json.dumps(message)
        dead_clients = []
        for cid, data in self.rooms[meeting_id].items():
            if cid == sender_client_id:
                continue
            try:
                await data["websocket"].send_text(payload)
            except Exception as e:
                logger.warning(f"Failed sending to {cid}: {e}")
                dead_clients.append(cid)
        for cid in dead_clients:
            self.disconnect(meeting_id, cid)


manager = ConnectionManager()


@router.websocket("/ws/meetings/{meeting_id}/{client_id}")
async def websocket_signaling_endpoint(
    websocket: WebSocket,
    meeting_id: str,
    client_id: str
):
    # Retrieve query param display_name safely
    display_name = websocket.query_params.get("display_name", "Participant")
    
    await manager.connect(meeting_id, client_id, display_name, websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                continue

            msg_type = data.get("type")
            target = data.get("target")

            if msg_type in ["offer", "answer", "ice-candidate"]:
                # Point-to-point WebRTC signaling message
                data["sender"] = client_id
                if target:
                    await manager.send_to_client(meeting_id, target, data)
            elif msg_type == "chat-message":
                # In-meeting chat message broadcast
                data["sender"] = client_id
                data["displayName"] = display_name
                await manager.broadcast_to_room(meeting_id, data)
            elif msg_type == "media-state":
                # Mute or video toggle broadcast
                data["sender"] = client_id
                if meeting_id in manager.rooms and client_id in manager.rooms[meeting_id]:
                    if "audio" in data:
                        manager.rooms[meeting_id][client_id]["audio"] = bool(data["audio"])
                    if "video" in data:
                        manager.rooms[meeting_id][client_id]["video"] = bool(data["video"])
                await manager.broadcast_to_others(meeting_id, client_id, data)
            elif msg_type == "reaction":
                # Real-time emoji reaction broadcast
                data["sender"] = client_id
                data["displayName"] = display_name
                await manager.broadcast_to_room(meeting_id, data)
            elif msg_type == "screen-state":
                # Screen share start/stop broadcast
                data["sender"] = client_id
                data["displayName"] = display_name
                if meeting_id in manager.rooms and client_id in manager.rooms[meeting_id]:
                    manager.rooms[meeting_id][client_id]["screen"] = bool(data.get("isSharing", False))
                await manager.broadcast_to_others(meeting_id, client_id, data)
            elif msg_type == "mute-all":
                # Host muted all participants
                await manager.broadcast_to_others(meeting_id, client_id, {
                    "type": "mute-all",
                    "sender": client_id
                })
            elif msg_type == "remove-peer":
                # Host removed specific peer
                if target:
                    await manager.send_to_client(meeting_id, target, {
                        "type": "removed-by-host",
                        "message": "You were removed from the meeting by the host."
                    })
            elif msg_type == "meeting-ended":
                # Host ended the meeting for everyone
                await manager.broadcast_to_room(meeting_id, {
                    "type": "meeting-ended",
                    "message": "The host has ended this meeting."
                })
            else:
                # General broadcast
                data["sender"] = client_id
                await manager.broadcast_to_others(meeting_id, client_id, data)

    except WebSocketDisconnect:
        manager.disconnect(meeting_id, client_id)
        await manager.broadcast_to_others(meeting_id, client_id, {
            "type": "peer-left",
            "clientId": client_id
        })
    except Exception as e:
        logger.error(f"Signaling error for {client_id}: {e}")
        manager.disconnect(meeting_id, client_id)
        await manager.broadcast_to_others(meeting_id, client_id, {
            "type": "peer-left",
            "clientId": client_id
        })
