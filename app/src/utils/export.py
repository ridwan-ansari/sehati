import pandas as pd
from io import BytesIO
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Class untuk mengekspor data kesehatan ke Excel (Async)"""
    
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
        
        # WIB timezone (UTC+7)
        wib = timezone(timedelta(hours=7))
        
        # Jika datetime sudah punya timezone, convert ke WIB
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt_wib = dt.astimezone(wib)
            # Remove timezone info untuk Excel
            return dt_wib.replace(tzinfo=None)
        
        # Jika tidak ada timezone, assume UTC dan convert ke WIB
        dt_utc = dt.replace(tzinfo=timezone.utc)
        dt_wib = dt_utc.astimezone(wib)
        return dt_wib.replace(tzinfo=None)
    
    async def get_users_data(self) -> pd.DataFrame:
        """Ambil data demografis users"""
        stmt = select(User).where(User.active == True)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        data = []
        for user in users:
            data.append({
                'user_id': user.id,
                'gender': user.gender,
                'age': self.calculate_age(user.date_of_birth),
                'date_of_birth': user.date_of_birth,
                'verified': user.verified,
                'created_at': self.convert_to_wib(user.created_at),
                'role': user.role
            })
        
        return pd.DataFrame(data)
    
    async def get_nutrition_data(self) -> pd.DataFrame:
        """Ambil data nutrisi dan antropometri"""
        stmt = select(UserNutrition).join(User).where(User.active == True)
        result = await self.db.execute(stmt)
        nutritions = result.scalars().all()
        
        data = []
        for nutrition in nutritions:
            # Ambil user data
            user_stmt = select(User).where(User.id == nutrition.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                data.append({
                    'user_id': nutrition.user_id,
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
    
    async def get_food_habit_data(self) -> pd.DataFrame:
        """Ambil data kebiasaan makan"""
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
            # Ambil user data
            user_stmt = select(User).where(User.id == answer.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                data.append({
                    'user_id': answer.user_id,
                    'gender': user.gender,
                    'age': age,
                    'category': answer.question.category,
                    'question': answer.question.question,
                    'answer': 'Ya' if answer.answer else 'Tidak',
                    'frequency': answer.frequency,
                    'recorded_at': self.convert_to_wib(answer.created_at)
                })
        
        return pd.DataFrame(data)
    
    async def get_food_diary_data(self) -> pd.DataFrame:
        """Ambil data diary makanan"""
        stmt = (
            select(FoodDiaryAnalysis)
            .join(User)
            .where(User.active == True)
            .options(joinedload(FoodDiaryAnalysis.items).joinedload(FoodDiaryItem.food))
        )
        result = await self.db.execute(stmt)
        analyses = result.unique().scalars().all()
        
        data = []
        for analysis in analyses:
            # Ambil user data
            user_stmt = select(User).where(User.id == analysis.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                
                # Data per item makanan
                for item in analysis.items:
                    calories_consumed = 0
                    if item.food and item.weight_grams:
                        calories_consumed = (item.food.calories * item.weight_grams) / 100
                    
                    data.append({
                        'user_id': analysis.user_id,
                        'gender': user.gender,
                        'age': age,
                        'diary_id': analysis.id,
                        'meal_type': item.meal_type,
                        'food_name': item.food.name if item.food else 'Unknown',
                        'food_category': item.food.category if item.food else None,
                        'quantity': item.quantity,
                        'weight_grams': item.weight_grams,
                        'calories_per_100g': item.food.calories if item.food else 0,
                        'calories_consumed': calories_consumed,
                        'energy_requirement': analysis.energy_requirement,
                        'desired_energy_requirement': analysis.desired_energy_requirement,
                        'total_daily_calories': analysis.total_calories,
                        'activity_level': analysis.activity,
                        'recorded_at': self.convert_to_wib(analysis.created_at)
                    })
        
        return pd.DataFrame(data)
    
    async def get_exercise_habit_data(self) -> pd.DataFrame:
        """Ambil data kebiasaan olahraga"""
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
            # Ambil user data
            user_stmt = select(User).where(User.id == answer.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                data.append({
                    'user_id': answer.user_id,
                    'gender': user.gender,
                    'age': age,
                    'category': answer.question.category,
                    'question': answer.question.question,
                    'question_type': answer.question.question_type,
                    'selected_option': answer.selected_option,
                    'answer_text': answer.answer_text,
                    'recorded_at': answer.recorded_at
                })
        
        return pd.DataFrame(data)
    
    async def get_sleep_data(self) -> pd.DataFrame:
        """Ambil data pola tidur"""
        stmt = (
            select(Sleep)
            .join(User)
            .where(User.active == True)
        )
        result = await self.db.execute(stmt)
        sleep_records = result.scalars().all()
        
        data = []
        for sleep in sleep_records:
            # Ambil user data
            user_stmt = select(User).where(User.id == sleep.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                age = self.calculate_age(user.date_of_birth)
                
                # Hitung durasi aktual jika ada waktu tidur dan bangun
                actual_duration = None
                duration_diff = None
                if sleep.sleep_time and sleep.wake_up_time:
                    actual_duration = sleep.actual_duration_minutes
                    if sleep.target_sleep_hours:
                        target_minutes = sleep.target_sleep_hours * 60
                        duration_diff = actual_duration - target_minutes
                
                data.append({
                    'user_id': sleep.user_id,
                    'gender': user.gender,
                    'age': age,
                    'sleep_time': self.convert_to_wib(sleep.sleep_time),
                    'wake_up_time': self.convert_to_wib(sleep.wake_up_time),
                    'actual_duration_minutes': actual_duration,
                    'actual_duration_hours': round(actual_duration / 60, 2) if actual_duration else None,
                    'target_sleep_hours': sleep.target_sleep_hours,
                    'duration_difference_minutes': duration_diff,
                    'sleep_quality': 'Cukup' if duration_diff and duration_diff >= -30 else 'Kurang' if duration_diff else None,
                    'recorded_at': self.convert_to_wib(sleep.created_at)
                })
        
        return pd.DataFrame(data)
    
    async def get_bmi_reference_data(self) -> pd.DataFrame:
        """Ambil data referensi BMI (WHO/CDC standard)"""
        stmt = select(BMIReference)
        result = await self.db.execute(stmt)
        references = result.scalars().all()
        
        data = []
        for ref in references:
            data.append({
                'gender': ref.gender,
                'age_years': ref.age_years,
                'age_months': ref.age_months,
                'sd_minus_3': float(ref.sd_minus_3),
                'sd_minus_2': float(ref.sd_minus_2),
                'sd_minus_1': float(ref.sd_minus_1),
                'median': float(ref.median),
                'sd_plus_1': float(ref.sd_plus_1),
                'sd_plus_2': float(ref.sd_plus_2),
                'sd_plus_3': float(ref.sd_plus_3)
            })
        
        return pd.DataFrame(data)
    
    async def generate_excel(self, output_path: Optional[str] = None) -> BytesIO:
        """
        Generate file Excel dengan semua data
        
        Args:
            output_path: Path untuk menyimpan file (optional)
            
        Returns:
            BytesIO object yang berisi file Excel
        """
        # Buat BytesIO object
        output = BytesIO()
        
        # Buat Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Sheet 1: Data Demografis Users
            df_users = await self.get_users_data()
            if not df_users.empty:
                df_users.to_excel(writer, sheet_name='Demografi', index=False)
            
            # Sheet 2: Data Nutrisi & Antropometri
            df_nutrition = await self.get_nutrition_data()
            if not df_nutrition.empty:
                df_nutrition.to_excel(writer, sheet_name='Nutrisi & Antropometri', index=False)
            
            # Sheet 3: Kebiasaan Makan
            df_food_habit = await self.get_food_habit_data()
            if not df_food_habit.empty:
                df_food_habit.to_excel(writer, sheet_name='Kebiasaan Makan', index=False)
            
            # Sheet 4: Diary Makanan
            df_food_diary = await self.get_food_diary_data()
            if not df_food_diary.empty:
                df_food_diary.to_excel(writer, sheet_name='Diary Makanan', index=False)
            
            # Sheet 5: Kebiasaan Olahraga
            df_exercise = await self.get_exercise_habit_data()
            if not df_exercise.empty:
                df_exercise.to_excel(writer, sheet_name='Kebiasaan Olahraga', index=False)
            
            # Sheet 6: Pola Tidur
            df_sleep = await self.get_sleep_data()
            if not df_sleep.empty:
                df_sleep.to_excel(writer, sheet_name='Pola Tidur', index=False)
            
            # Sheet 7: Referensi BMI
            df_bmi_ref = await self.get_bmi_reference_data()
            if not df_bmi_ref.empty:
                df_bmi_ref.to_excel(writer, sheet_name='Referensi BMI', index=False)
            
            # Auto-adjust column width untuk semua sheet
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
        
        # Save to file jika path diberikan
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())
        
        # Reset pointer
        output.seek(0)
        return output