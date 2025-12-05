from __future__ import annotations
import json
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

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
async def chat_endpoint(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_async_session)
):
    sender_id = None

    try:
        token = websocket.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token_value = token.split(" ")[1]
        else:
            token_value = websocket.query_params.get("token")

        if not token_value:
            await websocket.close(code=4001)
            return

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
            message = await crud_chat.save_message(session, room.id, sender_id, text)

            await manager.send_to_user(
                receiver_id,
                json.dumps({
                    "room_id": room.id,
                    "room_key": room.room_key,
                    "from": sender_id,
                    "message": text,
                    "created_at": str(message.created_at + timedelta(hours=7))
                })
            )

            await websocket.send_text(json.dumps({
                "room_id": room.id,
                "room_key": room.room_key,
                "to": receiver_id,
                "message": text,
                "status": "sent",
                "created_at": str(message.created_at + timedelta(hours=7))
            }))

    except WebSocketDisconnect:
        manager.disconnect(sender_id)
    except Exception as e:
        print("WebSocket Error:", e)
        manager.disconnect(sender_id)
        await websocket.close(code=1011)


@router.get("/messages/{room_key}")
async def get_messages(
    room_key: str,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        data = []

        room = await crud_chat.get_user_room_by_key(
            session=session,
            room_key=room_key,
            user_id=authentication.get("id")
        )

        if room:
            messages = await crud_chat.get_messages(
                session=session,
                room_id=room.id,
                limit=limit,
                offset=offset
            )
            for message in messages:
                item = {
                    "id": message.id,
                    "message": message.message,
                    "created_at": message.created_at + timedelta(hours=7),
                    "type": "sender" if message.sender_id == authentication["id"] else "receiver"
                }
                data.append(item)

        response.status_code = 200
        response.message = "Get Messages Successfully."
        response.data = data
    return response.build()


@router.get("/rooms")
async def get_rooms(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        rooms = await crud_chat.get_user_rooms(
            session=session,
            user_id=authentication["id"],
            limit=limit,
            offset=offset
        )
        response.status_code = 200
        response.message = "Get Rooms Successfully."
        response.data = rooms
    return response.build()
