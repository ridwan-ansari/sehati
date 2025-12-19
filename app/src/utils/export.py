import pandas as pd
from io import BytesIO
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import joinedload
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
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(self.wib).replace(tzinfo=None)

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
            'DOB': u.date_of_birth,
            'Status': 'Active' if u.active else 'Inactive',
            'Registered At': self._localize(u.created_at)
        } for u in users])

    async def get_nutrition_data(self):
        stmt = select(UserNutrition).options(joinedload(UserNutrition.user))
        result = await self.db.execute(stmt)
        data = []
        for n in result.scalars().all():
            if n.user:
                data.append({
                    'Nickname': n.user.nickname,
                    'Height (cm)': n.height_cm,
                    'Weight (kg)': n.weight_kg,
                    'BMI': n.bmi,
                    'Status': n.status,
                    'Recorded At': self._localize(n.created_at)
                })
        return pd.DataFrame(data)

    async def get_habit_data(self, model_class):
        stmt = select(model_class).options(
            joinedload(model_class.user),
            joinedload(model_class.question)
        )
        result = await self.db.execute(stmt)
        data = []
        for a in result.scalars().all():
            val = getattr(a, 'selected_option', None) or ('Ya' if getattr(a, 'answer', None) else 'Tidak')
            data.append({
                'Nickname': a.user.nickname,
                'Date': self._localize(a.created_at or getattr(a, 'recorded_at', None)).date(),
                'Category': a.question.category,
                'Question': a.question.question,
                'Answer': val
            })
        
        df = pd.DataFrame(data)
        if df.empty: return df
        return df.pivot_table(index=['Nickname', 'Date'], columns='Question', values='Answer', aggfunc='first').reset_index()

    async def get_food_diary_data(self):
        stmt = select(FoodDiaryAnalysis).options(
            joinedload(FoodDiaryAnalysis.user),
            joinedload(FoodDiaryAnalysis.items).joinedload(FoodDiaryItem.food)
        )
        result = await self.db.execute(stmt)
        daily, detail = [], []
        for a in result.unique().scalars().all():
            dt = self._localize(a.created_at).date()
            daily.append({
                'Nickname': a.user.nickname, 'Date': dt, 'Goal': a.energy_requirement,
                'Consumed': a.total_calories, 'Diff': a.total_calories - a.energy_requirement
            })
            for i in a.items:
                cal = (i.food.calories * i.weight_grams / 100) if i.food else 0
                detail.append({
                    'Nickname': a.user.nickname, 'Date': dt, 'Meal': i.meal_type,
                    'Food': i.food.name if i.food else '?', 'Grams': i.weight_grams, 'Calories': cal
                })
        return pd.DataFrame(daily), pd.DataFrame(detail)

    async def get_sleep_data(self):
        result = await self.db.execute(select(Sleep).options(joinedload(Sleep.user)))
        data = []
        for s in result.scalars().all():
            dur = s.actual_duration_minutes / 60 if s.actual_duration_minutes else 0
            data.append({
                'Nickname': s.user.nickname,
                'Date': self._localize(s.sleep_time).date() if s.sleep_time else None,
                'Duration (Hrs)': round(dur, 2),
                'Quality': 'Good' if dur >= (s.target_sleep_hours or 7) else 'Poor'
            })
        return pd.DataFrame(data)

    def _apply_style(self, writer, sheet_name):
        ws = writer.sheets[sheet_name]
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            
        for col in ws.columns:
            max_len = max([len(str(cell.value)) for cell in col])
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    async def generate_excel(self) -> BytesIO:
        output = BytesIO()
        async_data = {
            'Demografi': self.get_users_data(),
            'Antropometri': self.get_nutrition_data(),
            'Habit_Makan': self.get_habit_data(FoodHabitAnswer),
            'Habit_Olahraga': self.get_habit_data(ExerciseHabitAnswer),
            'Pola_Tidur': self.get_sleep_data()
        }
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for name, task in async_data.items():
                df = await task
                if not df.empty:
                    df.to_excel(writer, sheet_name=name, index=False)
                    self._apply_style(writer, name)
            
            f_daily, f_detail = await self.get_food_diary_data()
            for n, d in [('Diary_Harian', f_daily), ('Diary_Detail', f_detail)]:
                if not d.empty:
                    d.to_excel(writer, sheet_name=n, index=False)
                    self._apply_style(writer, n)

        output.seek(0)
        return output