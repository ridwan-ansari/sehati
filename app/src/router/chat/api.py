from __future__ import annotations
import json
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Body

from app.src.core.security import AuthService
from app.src.router.chat.crud import CRUDChat
from app.src.router.user.crud import CRUDUser
from app.src.utils.fcm_client import fcm_client
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.i18n import get_lang, t
from app.src.utils.connection_manager import ConnectionManager

router = APIRouter()
ws_router = APIRouter()
crud_chat = CRUDChat()
crud_user = CRUDUser()
auth_service = AuthService()
manager = ConnectionManager()


def _resolve_lang(accept_language: str) -> str:
    primary = accept_language.split(",")[0].split(";")[0].split("-")[0].strip().lower()
    return primary if primary in ("en", "id") else "en"


@ws_router.websocket("/chat")
async def chat_endpoint(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_async_session),
):
    sender_id = None
    lang = _resolve_lang(websocket.headers.get("accept-language", "en"))

    try:
        token = websocket.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token_value = token.split(" ")[1]
        else:
            token_value = websocket.query_params.get("token")

        if not token_value:
            await websocket.close(code=4001)
            return

        payload = await auth_service._decode_token(token_value, lang)
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
                await websocket.send_text(json.dumps({"error": t("chat_invalid_format", lang)}))
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
                    "created_at": str(message.created_at + timedelta(hours=7)),
                }),
            )

            await websocket.send_text(json.dumps({
                "room_id": room.id,
                "room_key": room.room_key,
                "to": receiver_id,
                "message": text,
                "status": "sent",
                "created_at": str(message.created_at + timedelta(hours=7)),
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
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        data = []
        room = await crud_chat.get_user_room_by_key(
            session=session, room_key=room_key, user_id=authentication.get("id")
        )
        if room:
            messages = await crud_chat.get_messages(
                session=session, room_id=room.id, limit=limit, offset=offset
            )
            for message in messages:
                data.append({
                    "id": message.id,
                    "message": message.message,
                    "created_at": message.created_at + timedelta(hours=7),
                    "type": "sender" if message.sender_id == authentication["id"] else "receiver",
                })
        response.status_code = 200
        response.message = t("messages_success", lang)
        response.data = data
    return response.build()


@router.get("/rooms")
async def get_rooms(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        rooms = await crud_chat.get_user_rooms(
            session=session, user_id=authentication["id"], limit=limit, offset=offset
        )
        response.status_code = 200
        response.message = t("rooms_success", lang)
        response.data = rooms
    return response.build()


@router.post("/send-chat-notif")
async def send_chat_notif(
    receiver_id: str = Body(...),
    message: str = Body(...),
    room_key: str = Body(...),
    room_id: str = Body(...),
    token_fcm: str | None = Body(default=None),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        # sender identity always comes from the JWT, never the request body — otherwise
        # any authenticated user could spoof push notifications as any other user.
        sender = await crud_user.get_user_by_id(session=session, id=authentication["id"])
        receiver = await crud_user.get_user_by_id(session=session, id=receiver_id)
        target_token = token_fcm or (receiver.fcm_token if receiver else None)

        if target_token:
            _, is_invalid = await fcm_client.send(
                token=target_token,
                title=sender.fullname if sender else "SEHATI",
                body=message,
                data={
                    "type": "chat",
                    "room_id": room_id,
                    "room_key": room_key,
                    "sender_id": authentication["id"],
                    "sender_picture": (sender.picture or "") if sender else "",
                },
            )
            if is_invalid and receiver:
                await crud_user.update_fcm_token(session=session, user_id=receiver.id, token=None)

        response.status_code = 200
        response.message = t("chat_notif_sent", lang)
    return response.build()
