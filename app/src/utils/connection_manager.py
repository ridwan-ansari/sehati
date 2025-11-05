from __future__ import annotations
from typing import Dict
from loguru import logger
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"✅ [Connect] User {user_id} connected.")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.warning(f"❌ [Disconnect] User {user_id} disconnected.")

    async def send_to_user(self, user_id: int, message: str):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)
            logger.add(f"📤 [Send] Message sent to user {user_id}")

    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)
        logger.info(f"📣 [Broadcast] Message broadcast to {len(self.active_connections)} users.")

    def get_online_users(self):
        return list(self.active_connections.keys())
