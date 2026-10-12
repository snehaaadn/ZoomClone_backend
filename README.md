# Zoom Clone — Backend (FastAPI & SQLite)

High-performance video conferencing REST API and real-time WebRTC signaling server built with **FastAPI**, **SQLAlchemy 2.0**, and **WebSockets**.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- virtualenv / pip

### 2. Setup & Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run automated test suite (16 tests)
pytest tests/ -v

# Start development server (runs on http://localhost:8000)
python run.py
```

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 📡 API Endpoints Overview

- `GET /api/health` — Health check
- `GET /api/meetings/upcoming` — List scheduled & active meetings
- `GET /api/meetings/recent` — List completed & cancelled meetings
- `POST /api/meetings/instant` — Create instant 10-digit meeting
- `POST /api/meetings/schedule` — Schedule future meeting
- `GET /api/meetings/{id}/validate` — Pre-join meeting validation
- `GET /api/meetings/{id}` — Retrieve meeting details
- `POST /api/meetings/{id}/join` — Join meeting as attendee/host
- `POST /api/meetings/{id}/leave` — Leave meeting
- `POST /api/meetings/{id}/end` — End meeting for all (host control)
- `POST /api/meetings/{id}/cancel` — Cancel meeting
- `DELETE /api/meetings/{id}` — Delete meeting permanently
- `PATCH /api/participants/{id}` — Update audio/video/mute state
- `DELETE /api/participants/{id}` — Remove participant (host control)
- `WS /ws/meetings/{meeting_id}/{client_id}` — Real-time WebRTC signaling, chat, reactions & host controls
