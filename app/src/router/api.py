from fastapi import APIRouter
from app.src.router.auth.api import router as auth
from app.src.router.user.api import router as user
from app.src.router.chat.api import router as chat
from app.src.router.chat.api import ws_router as ws_chat
from app.src.router.dashboard.api import router as dashboard
from app.src.router.user_nutrition.api import router as user_nutrition

router = APIRouter(prefix="/api")
router.include_router(user, prefix="/user", tags=["User"])
router.include_router(chat, prefix="/chat", tags=["Chat"])
router.include_router(ws_chat, prefix="/ws", tags=["Chat"])
router.include_router(auth, prefix="/auth", tags=["Authentication"])
router.include_router(user_nutrition, prefix="/user/nutrition", tags=["User Nutritions"])

router_dashboard = APIRouter()
router_dashboard.include_router(dashboard, prefix="/dashboard", tags=["Admin Dashboard"])
