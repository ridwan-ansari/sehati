from fastapi import APIRouter
from app.src.router.chat.api import router as chat_router
from app.src.router.auth.api import router as auth_router
from app.src.router.user.api import router as user_router
from app.src.router.food.api import router as food_router
from app.src.router.games.api import router as game_router
from app.src.router.sleep.api import router as sleep_router
from app.src.router.video.api import router as video_router
from app.src.router.point.api import router as point_router
from app.src.router.forum.api import router as forum_router
from app.src.router.recipe.api import router as recipe_router
from app.src.router.exercise.api import router as exercise_router
from app.src.router.reminder.api import router as reminder_router
from app.src.router.dashboard.api import router as dashboard_router
from app.src.router.merchandise.api import router as merchandise_router
from app.src.router.appointment.api import router as appointment_router
from app.src.router.user_nutrition.api import router as user_nutrition_router

router = APIRouter(prefix="/api")

router.include_router(game_router, prefix="/games", tags=["Games"]) 
router.include_router(forum_router, prefix="/forum", tags=["Forum"]) 
router.include_router(sleep_router, prefix="/sleep", tags=["Sleep"]) 
router.include_router(chat_router, prefix="/chat", tags=["Chat System"])
router.include_router(video_router, prefix="/video", tags=["Video List"])
router.include_router(point_router, prefix="/point", tags=["Leaderboard"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(recipe_router, prefix="/recipe", tags=["Recipe List"])
router.include_router(user_router, prefix="/users", tags=["User Management"])
router.include_router(food_router, prefix="/habit", tags=["Food & Nutrition"])
router.include_router(exercise_router, prefix="/exercise", tags=["Exercise Habit"])
router.include_router(reminder_router, prefix="/reminders", tags=["Reminders"])
router.include_router(appointment_router, prefix="/appointment", tags=["Appointment"])
router.include_router(user_nutrition_router, prefix="/user/nutrition", tags=["User Nutrition Tracking"])
router.include_router(merchandise_router, prefix="/merchandise", tags=["Merchandise"])

router_dashboard = APIRouter()
router_dashboard.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])
