"""
Health Data Excel Export Module (Async Version) - Enhanced for Research
Ekspor data kesehatan ke Excel untuk penelitian kedokteran dengan visualisasi
"""

import pandas as pd
from io import BytesIO
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows

from app.src.models.user import User
from app.src.models.user_nutrition import UserNutrition
from app.src.models.bmi_reference import BMIReference
from app.src.models.food import (
    FoodHabitQuestion, FoodHabitAnswer, 
    FoodDiaryAnalysis, FoodDiaryItem
)
from app.src.models.exercise_habit import (
    ExerciseHabitQuestion, ExerciseHabitAnswer
)
from app.src.models.sleep import Sleep


class HealthDataExcelExporter:
    """Class untuk mengekspor data kesehatan ke Excel (Async) dengan visualisasi"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def calculate_age(self, date_of_birth) -> Optional[int]:
        """Hitung umur dari tanggal lahir"""
        if not date_of_birth:
            return None
        today = datetime.now().date()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
    
    def convert_to_wib(self, dt):
        """Convert datetime ke WIB (UTC+7) dan remove timezone untuk Excel compatibility"""
        if dt is None:
            return None
        
        from datetime import timezone, timedelta
        wib = timezone(timedelta(hours=7))
        
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt_wib = dt.astimezone(wib)
            return dt_wib.replace(tzinfo=None)
        
        dt_utc = dt.replace(tzinfo=timezone.utc)
        dt_wib = dt_utc.astimezone(wib)
        return dt_wib.replace(tzinfo=None)
    
    async def get_users_data(self) -> pd.DataFrame:
        """Ambil data demografis users dengan nickname"""
        stmt = select(User).where(User.active == True)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        data = []
        for user in users:
            data.append({
                'nickname': user.nickname,
                'gender': user.gender,
                'age': self.calculate_age(user.date_of_birth),
                'date_of_birth': user.date_of_birth,
                'verified': user.verified,
                'registered_at': self.convert_to_wib(user.created_at),
                'role': user.role
            })
        
        return pd.DataFrame(data)
    
    async def get_nutrition_data(self) -> pd.DataFrame:
        """Ambil data nutrisi dan antropometri dengan nickname"""
        stmt = select(UserNutrition).join(User).where(User.active == True)
        result = await self.db.execute(stmt)
        nutritions = result.scalars().all()
        
        data = []
        for nutrition in nutritions:
            user_stmt = select(User).where(User.id == nutrition.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                data.append({
                    'nickname': user.nickname,
                    'gender': user.gender,
                    'age': age,
                    'height_cm': nutrition.height_cm,
                    'weight_kg': nutrition.weight_kg,
                    'bmi': nutrition.bmi,
                    'ideal_weight_kg': nutrition.ideal_weight_kg,
                    'nutritional_status': nutrition.status,
                    'recorded_at': self.convert_to_wib(nutrition.created_at)
                })
        
        return pd.DataFrame(data)
    
    async def get_food_habit_summary(self) -> pd.DataFrame:
        """Ambil ringkasan kebiasaan makan per user (pivot format)"""
        stmt = (
            select(FoodHabitAnswer)
            .join(User)
            .join(FoodHabitQuestion)
            .where(User.active == True)
            .options(joinedload(FoodHabitAnswer.question))
        )
        result = await self.db.execute(stmt)
        answers = result.unique().scalars().all()
        
        data = []
        for answer in answers:
            user_stmt = select(User).where(User.id == answer.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                data.append({
                    'nickname': user.nickname,
                    'category': answer.question.category,
                    'question': answer.question.question,
                    'answer': 'Ya' if answer.answer else 'Tidak',
                    'frequency': answer.frequency,
                    'date': self.convert_to_wib(answer.created_at).date() if answer.created_at else None
                })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Create pivot table: rows=nickname, columns=question, values=answer
        pivot = df.pivot_table(
            index=['nickname', 'date'],
            columns='question',
            values='answer',
            aggfunc='first'
        ).reset_index()
        
        return pivot
    
    async def get_food_diary_daily(self) -> pd.DataFrame:
        """Ambil data diary makanan dikelompokkan per hari per user"""
        stmt = (
            select(FoodDiaryAnalysis)
            .join(User)
            .where(User.active == True)
            .options(joinedload(FoodDiaryAnalysis.items).joinedload(FoodDiaryItem.food))
        )
        result = await self.db.execute(stmt)
        analyses = result.unique().scalars().all()
        
        # Data summary per hari
        daily_data = []
        # Data detail per makanan
        detail_data = []
        
        for analysis in analyses:
            user_stmt = select(User).where(User.id == analysis.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                date = self.convert_to_wib(analysis.created_at).date() if analysis.created_at else None
                
                # Summary per hari
                daily_data.append({
                    'nickname': user.nickname,
                    'date': date,
                    'energy_requirement': analysis.energy_requirement,
                    'desired_energy': analysis.desired_energy_requirement,
                    'total_calories_consumed': analysis.total_calories,
                    'calorie_difference': analysis.total_calories - analysis.energy_requirement,
                    'activity_level': analysis.activity,
                    'meal_count': len(analysis.items)
                })
                
                # Detail per item makanan
                for item in analysis.items:
                    calories = 0
                    if item.food and item.weight_grams:
                        calories = (item.food.calories * item.weight_grams) / 100
                    
                    detail_data.append({
                        'nickname': user.nickname,
                        'date': date,
                        'meal_type': item.meal_type,
                        'food_name': item.food.name if item.food else 'Unknown',
                        'food_category': item.food.category if item.food else None,
                        'quantity': item.quantity,
                        'weight_grams': item.weight_grams,
                        'calories': calories
                    })
        
        return pd.DataFrame(daily_data), pd.DataFrame(detail_data)
    
    async def get_exercise_habit_summary(self) -> pd.DataFrame:
        """Ambil ringkasan kebiasaan olahraga per user (pivot format)"""
        stmt = (
            select(ExerciseHabitAnswer)
            .join(User)
            .join(ExerciseHabitQuestion)
            .where(User.active == True)
            .options(joinedload(ExerciseHabitAnswer.question))
        )
        result = await self.db.execute(stmt)
        answers = result.unique().scalars().all()
        
        data = []
        for answer in answers:
            user_stmt = select(User).where(User.id == answer.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                data.append({
                    'nickname': user.nickname,
                    'category': answer.question.category,
                    'question': answer.question.question,
                    'answer': answer.selected_option or answer.answer_text or '-',
                    'date': answer.recorded_at
                })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Create pivot table
        pivot = df.pivot_table(
            index=['nickname', 'date'],
            columns='question',
            values='answer',
            aggfunc='first'
        ).reset_index()
        
        return pivot
    
    async def get_sleep_daily(self) -> pd.DataFrame:
        """Ambil data tidur per hari per user"""
        stmt = select(Sleep).join(User).where(User.active == True)
        result = await self.db.execute(stmt)
        sleep_records = result.scalars().all()
        
        data = []
        for sleep in sleep_records:
            user_stmt = select(User).where(User.id == sleep.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                actual_hours = None
                duration_diff = None
                quality = None
                
                if sleep.sleep_time and sleep.wake_up_time:
                    actual_minutes = sleep.actual_duration_minutes
                    actual_hours = round(actual_minutes / 60, 2)
                    
                    if sleep.target_sleep_hours:
                        target_minutes = sleep.target_sleep_hours * 60
                        duration_diff = actual_minutes - target_minutes
                        quality = 'Cukup' if duration_diff >= -30 else 'Kurang'
                
                data.append({
                    'nickname': user.nickname,
                    'date': self.convert_to_wib(sleep.sleep_time).date() if sleep.sleep_time else None,
                    'sleep_time': self.convert_to_wib(sleep.sleep_time),
                    'wake_up_time': self.convert_to_wib(sleep.wake_up_time),
                    'actual_hours': actual_hours,
                    'target_hours': sleep.target_sleep_hours,
                    'difference_minutes': duration_diff,
                    'sleep_quality': quality
                })
        
        return pd.DataFrame(data)
    
    async def get_nutrition_status_stats(self) -> pd.DataFrame:
        """Statistik status gizi untuk visualisasi"""
        stmt = select(UserNutrition).join(User).where(User.active == True)
        result = await self.db.execute(stmt)
        nutritions = result.scalars().all()
        
        status_counts = {}
        for nutrition in nutritions:
            status = nutrition.status or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        data = [{'nutritional_status': k, 'count': v} for k, v in status_counts.items()]
        return pd.DataFrame(data)
    
    def add_chart_to_sheet(self, worksheet, df, chart_type='bar', title='', position='H2'):
        """Tambahkan chart ke worksheet"""
        if df.empty or len(df.columns) < 2:
            return
        
        if chart_type == 'pie':
            chart = PieChart()
        else:
            chart = BarChart()
        
        chart.title = title
        chart.height = 10
        chart.width = 20
        
        # Add data to chart
        data = Reference(worksheet, min_col=2, min_row=1, max_row=len(df) + 1, max_col=2)
        cats = Reference(worksheet, min_col=1, min_row=2, max_row=len(df) + 1)
        
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        
        worksheet.add_chart(chart, position)
    
    async def generate_excel(self, output_path: Optional[str] = None) -> BytesIO:
        """
        Generate file Excel dengan semua data, visualisasi, dan grouping yang rapi
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # ===== SHEET 1: DEMOGRAFI =====
            df_users = await self.get_users_data()
            if not df_users.empty:
                df_users.to_excel(writer, sheet_name='1_Demografi', index=False)
            
            # ===== SHEET 2: NUTRISI & ANTROPOMETRI =====
            df_nutrition = await self.get_nutrition_data()
            if not df_nutrition.empty:
                df_nutrition.to_excel(writer, sheet_name='2_Nutrisi_Antropometri', index=False)
            
            # ===== SHEET 3: STATISTIK STATUS GIZI + CHART =====
            df_nutrition_stats = await self.get_nutrition_status_stats()
            if not df_nutrition_stats.empty:
                df_nutrition_stats.to_excel(writer, sheet_name='3_Stats_Status_Gizi', index=False)
                ws = writer.sheets['3_Stats_Status_Gizi']
                self.add_chart_to_sheet(ws, df_nutrition_stats, 'pie', 'Distribusi Status Gizi', 'E2')
            
            # ===== SHEET 4: KEBIASAAN MAKAN (PIVOT) =====
            df_food_habit = await self.get_food_habit_summary()
            if not df_food_habit.empty:
                df_food_habit.to_excel(writer, sheet_name='4_Kebiasaan_Makan', index=False)
            
            # ===== SHEET 5 & 6: DIARY MAKANAN =====
            df_food_daily, df_food_detail = await self.get_food_diary_daily()
            if not df_food_daily.empty:
                df_food_daily.to_excel(writer, sheet_name='5_Diary_Harian', index=False)
            if not df_food_detail.empty:
                df_food_detail.to_excel(writer, sheet_name='6_Diary_Detail', index=False)
            
            # ===== SHEET 7: KEBIASAAN OLAHRAGA (PIVOT) =====
            df_exercise = await self.get_exercise_habit_summary()
            if not df_exercise.empty:
                df_exercise.to_excel(writer, sheet_name='7_Kebiasaan_Olahraga', index=False)
            
            # ===== SHEET 8: POLA TIDUR PER HARI =====
            df_sleep = await self.get_sleep_daily()
            if not df_sleep.empty:
                df_sleep.to_excel(writer, sheet_name='8_Pola_Tidur', index=False)
            
            # Auto-adjust column width
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())
        
        output.seek(0)
        return output