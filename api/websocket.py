"""
WebSocket Manager for Real-time Updates
"""
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


class JobManager:
    """Manages WebSocket connections for job updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.job_subscriptions: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        # Remove from all subscriptions
        for job_id in list(self.job_subscriptions.keys()):
            self.job_subscriptions[job_id].discard(websocket)
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
    
    def subscribe(self, websocket: WebSocket, job_id: int):
        """Subscribe to updates for a specific job."""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(websocket)
    
    async def broadcast(self, job_id: int, message: dict):
        """Broadcast a message to all subscribers of a job."""
        message["job_id"] = job_id
        json_message = json.dumps(message)
        
        # If job_id is -1, broadcast to all connections (for analysis updates)
        if job_id == -1:
            for websocket in list(self.active_connections):
                try:
                    await websocket.send_text(json_message)
                except Exception:
                    self.disconnect(websocket)
        else:
            # Broadcast to job subscribers
            if job_id in self.job_subscriptions:
                for websocket in list(self.job_subscriptions[job_id]):
                    try:
                        await websocket.send_text(json_message)
                    except Exception:
                        self.disconnect(websocket)
            
            # Also broadcast to all connections for job list updates
            for websocket in list(self.active_connections):
                try:
                    await websocket.send_text(json_message)
                except Exception:
                    self.disconnect(websocket)


# Global job manager instance
job_manager = JobManager()


@router.websocket("/jobs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for job updates."""
    await job_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle subscription requests
                if message.get("type") == "subscribe" and "job_id" in message:
                    job_manager.subscribe(websocket, message["job_id"])
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "job_id": message["job_id"],
                    }))
                
                # Handle ping
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        job_manager.disconnect(websocket)
