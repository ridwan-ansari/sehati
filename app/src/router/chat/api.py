from __future__ import annotations
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.router.chat.crud import CRUDChat
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.connection_manager import ConnectionManager

router = APIRouter()
ws_router = APIRouter()
crud_chat = CRUDChat()
auth_service = AuthService()
manager = ConnectionManager()

@ws_router.websocket("/chat")
async def chat_endpoint(websocket: WebSocket, session: AsyncSession = Depends(get_async_session)):
    try:
        token = websocket.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            await websocket.close(code=4001)
            return

        token_value = token.split(" ")[1]
        payload = await auth_service._decode_token(token_value)
        sender_id = payload.get("id")
        if not sender_id:
            await websocket.close(code=4003)
            return

        await manager.connect(websocket, sender_id)

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            receiver_id = msg.get("to")
            text = msg.get("message")

            if not receiver_id or not text:
                await websocket.send_text(json.dumps({
                    "error": "Invalid message format. Required: {to, message}"
                }))
                continue

            room = await crud_chat.get_or_create_room(session, sender_id, receiver_id)
            await crud_chat.save_message(session, room.id, sender_id, text)

            await manager.send_to_user(
                receiver_id,
                json.dumps({
                    "room_id": room.id,
                    "from": sender_id,
                    "message": text
                })
            )

            await websocket.send_text(json.dumps({
                "room_id": room.id,
                "to": receiver_id,
                "message": text,
                "status": "sent"
            }))

    except WebSocketDisconnect:
        manager.disconnect(sender_id)
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        manager.disconnect(sender_id)
        await websocket.close(code=1011)

@router.get("/messages/{room_key}")
async def get_messages(
    user_id: str,
    room_key: str,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        data = []
        room = await crud_chat.get_user_room_by_key(session=session, room_key=room_key, user_id=user_id)
        if room:
            messages = await crud_chat.get_messages(session=session, room_id=room.id, limit=limit, offset=offset)
            for message in messages:
                msg = {"id":message.id,"message":message.message, "created_at":message.created_at}
                if message.sender_id == auth.get("id"):
                    msg.update({"type":"sender"})
                else:
                    msg.update({"type":"receiver"})
                data.append(msg)
        response.status_code = 200
        response.message = "Get Messages Successfully."
        response.data = data
    return response.build()

@router.get("/rooms")
async def get_rooms(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        data = await crud_chat.get_user_rooms(session=session, user_id=auth.get("id"), limit=limit, offset=offset)
        response.status_code = 200
        response.message = "Get Rooms Successfully."
        response.data = data
    return response.build()