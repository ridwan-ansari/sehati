from __future__ import annotations
import os
from loguru import logger
import firebase_admin
from firebase_admin import credentials, messaging
from app.src.core.config import settings

_initialized = False
if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
    firebase_admin.initialize_app(credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH))
    _initialized = True
else:
    logger.warning(f"Firebase credentials not found at {settings.FIREBASE_CREDENTIALS_PATH}; push notifications are disabled.")


class FCMClient:
    async def send(self, token: str, title: str, body: str, data: dict | None = None) -> tuple[str | None, bool]:
        """Send a push notification. Returns (message_id, token_is_invalid)."""
        if not _initialized:
            logger.error("Firebase is not initialized; skipping push notification.")
            return None, False

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        response = await messaging.send_each_async([message])
        result = response.responses[0]
        if result.success:
            return result.message_id, False

        is_invalid = isinstance(result.exception, messaging.UnregisteredError)
        logger.warning(f"FCM send failed for token {token[:12]}...: {result.exception}")
        return None, is_invalid


fcm_client = FCMClient()
