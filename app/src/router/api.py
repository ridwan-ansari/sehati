from fastapi import APIRouter
from app.src.router.auth.api import router as auth_router
from app.src.router.user.api import router as user_router
from app.src.router.chat.api import router as chat_router
from app.src.router.food.api import router as food_router
from app.src.router.video.api import router as video_router
from app.src.router.chat.api import ws_router as ws_chat_router
from app.src.router.dashboard.api import router as dashboard_router
from app.src.router.user_nutrition.api import router as user_nutrition_router

router = APIRouter(prefix="/api")

router.include_router(user_router, prefix="/users", tags=["User Management"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(chat_router, prefix="/chat", tags=["Chat System"])
router.include_router(video_router, prefix="/video", tags=["Video List"])
router.include_router(ws_chat_router, prefix="/ws", tags=["Chat WebSocket"])
router.include_router(food_router, prefix="/habit", tags=["Food & Nutrition"])
router.include_router(user_nutrition_router, prefix="/user/nutrition", tags=["User Nutrition Tracking"])

router_dashboard = APIRouter()
router_dashboard.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])
