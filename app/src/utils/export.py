import pandas as pd
from io import BytesIO
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Font, Alignment, PatternFill

from app.src.models.user import User
from app.src.models.user_nutrition import UserNutrition
from app.src.models.food import FoodHabitAnswer, FoodDiaryAnalysis, FoodDiaryItem
from app.src.models.exercise_habit import ExerciseHabitAnswer
from app.src.models.sleep import Sleep


class HealthDataExcelExporter:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wib = timezone(timedelta(hours=7))

    def _localize(self, dt):
        if not dt: return None
        dt_utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return dt_utc.astimezone(self.wib).replace(tzinfo=None)

    def _calculate_age(self, dob):
        if not dob: return None
        today = datetime.now().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    async def get_users_data(self):
        result = await self.db.execute(select(User))
        users = result.scalars().all()
        return pd.DataFrame([{
            'Nickname': u.nickname,
            'Gender': u.gender,
            'Age': self._calculate_age(u.date_of_birth),
            'Status': 'Active' if u.active else 'Inactive',
            'Registered': self._localize(u.created_at)
        } for u in users])

    async def get_nutrition_data(self):
        stmt = select(UserNutrition).options(selectinload(UserNutrition.user))
        result = await self.db.execute(stmt)
        return pd.DataFrame([{
            'Nickname': n.user.nickname if n.user else 'N/A',
            'Height_cm': n.height_cm or 0,
            'Weight_kg': n.weight_kg or 0,
            'BMI': n.bmi or 0,
            'Status': n.status or 'Unknown',
            'Date': self._localize(n.created_at)
        } for n in result.scalars().all()])

    async def get_habit_pivot(self, model_class):
        stmt = select(model_class).options(
            selectinload(model_class.user),
            selectinload(model_class.question)
        )
        result = await self.db.execute(stmt)
        raw = []
        for a in result.scalars().all():
            if not (a.user and a.question): continue
            
            val = a.selected_option or a.answer_text or ('Ya' if getattr(a, 'answer', False) else 'Tidak')
            raw_date = a.created_at if hasattr(a, 'created_at') else getattr(a, 'recorded_at', None)
            
            raw.append({
                'Nickname': a.user.nickname,
                'Date': self._localize(raw_date).date() if raw_date else None,
                'Question': a.question.question,
                'Answer': val
            })
        
        df = pd.DataFrame(raw)
        if df.empty: return df
        return df.pivot_table(index=['Nickname', 'Date'], columns='Question', values='Answer', aggfunc='first').reset_index()

    async def get_food_diary_data(self):
        stmt = select(FoodDiaryAnalysis).options(
            selectinload(FoodDiaryAnalysis.user),
            selectinload(FoodDiaryAnalysis.items).selectinload(FoodDiaryItem.food)
        )
        result = await self.db.execute(stmt)
        daily, detail = [], []
        
        for a in result.unique().scalars().all():
            u_name = a.user.nickname if a.user else "Unknown"
            dt = self._localize(a.created_at).date() if a.created_at else None
            
            daily.append({
                'Nickname': u_name, 'Date': dt, 
                'Goal_Cal': a.energy_requirement or 0,
                'Consumed_Cal': a.total_calories or 0,
                'Diff': (a.total_calories or 0) - (a.energy_requirement or 0)
            })
            
            items = a.items or []
            for i in items:
                cal_per_100 = getattr(i.food, 'calories', 0) or 0
                weight = i.weight_grams or 0
                detail.append({
                    'Nickname': u_name, 'Date': dt, 'Meal': i.meal_type,
                    'Food': i.food.name if i.food else '?', 
                    'Grams': weight, 
                    'Calories': (cal_per_100 * weight) / 100
                })
        return pd.DataFrame(daily), pd.DataFrame(detail)

    def _apply_styling(self, writer, sheet_name):
        ws = writer.sheets[sheet_name]
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            
        for col in ws.columns:
            max_len = 0
            for cell in col:
                try: max_len = max(max_len, len(str(cell.value or "")))
                except: pass
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    async def generate_excel(self) -> BytesIO:
        output = BytesIO()
        async_tasks = {
            "1_Demographics": self.get_users_data(),
            "2_Body_Composition": self.get_nutrition_data(),
            "3_Food_Habits": self.get_habit_pivot(FoodHabitAnswer),
            "4_Exercise_Habits": self.get_habit_pivot(ExerciseHabitAnswer)
        }

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, task in async_tasks.items():
                df = await task
                if not df.empty:
                    df.to_excel(writer, sheet_name, index=False)
            
            f_daily, f_detail = await self.get_food_diary_data()
            if not f_daily.empty: f_daily.to_excel(writer, "5_Daily_Summary", index=False)
            if not f_detail.empty: f_detail.to_excel(writer, "6_Food_Logs", index=False)

            for sheet in writer.sheets:
                self._apply_styling(writer, sheet)

        output.seek(0)
        return output