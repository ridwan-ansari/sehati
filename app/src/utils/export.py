import pandas as pd
from io import BytesIO
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta, date
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from app.src.models.user import User
from app.src.models.user_nutrition import UserNutrition
from app.src.models.exercise_habit import ExerciseHabitAnswer
from app.src.models.sleep import Sleep
from app.src.models.food import FoodHabitAnswer, FoodDiaryAnalysis, FoodDiaryItem

class HealthDataExcelExporter:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wib = timezone(timedelta(hours=7))

    def _localize(self, dt):
        """Konversi UTC ke WIB untuk keperluan Excel"""
        if not dt: 
            return None
        # Jika sudah berupa date (bukan datetime), langsung return
        if isinstance(dt, date) and not isinstance(dt, datetime):
            return dt
        
        dt_utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return dt_utc.astimezone(self.wib).replace(tzinfo=None)

    def _calculate_age(self, dob):
        """Hitung umur dengan presisi dari objek date/datetime"""
        if not dob: 
            return None
        today = datetime.now(self.wib).date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    async def get_users_data(self):
        """Ambil data demografi user (exclude admin secara langsung di query)"""
        stmt = select(User).where(
            and_(
                User.role != 'admin',
                User.deleted_at.is_(None)
            )
        ).order_by(User.created_at.desc())
        
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return pd.DataFrame([{
            'Fullname': u.fullname,
            'Nickname': u.nickname,
            'Email': u.email,
            'Phone_Number': u.phone_number,
            'Gender': u.gender.value if hasattr(u.gender, 'value') else u.gender,
            'Date_of_Birth': u.date_of_birth,
            'Age': self._calculate_age(u.date_of_birth),
            'Active': 'Yes' if u.active else 'No',
            'Verified': 'Yes' if u.verified else 'No',
            'Created_At': self._localize(u.created_at)
        } for u in users])

    async def get_nutrition_data(self):
        """Ambil data nutrisi dengan join filter admin di SQL"""
        stmt = select(UserNutrition).join(User).where(
            and_(
                User.role != 'admin',
                UserNutrition.deleted_at.is_(None)
            )
        ).options(selectinload(UserNutrition.user)).order_by(UserNutrition.created_at.desc())
        
        result = await self.db.execute(stmt)
        nutritions = result.scalars().all()
        
        data = [{
            'Nickname': n.user.nickname if n.user else 'Unknown',
            'Height_cm': n.height_cm,
            'Weight_kg': n.weight_kg,
            'BMI': round(n.bmi, 2) if n.bmi else None,
            'Ideal_Weight_kg': n.ideal_weight_kg,
            'Status': n.status,
            'Created_At': self._localize(n.created_at),
            'Updated_At': self._localize(n.updated_at)
        } for n in nutritions]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(['Nickname', 'Created_At'], ascending=[True, False])
        return df

    async def get_sleep_records(self):
        """Ambil data pola tidur"""
        stmt = select(Sleep).join(User).where(
            and_(User.role != 'admin', Sleep.deleted_at.is_(None))
        ).options(selectinload(Sleep.user)).order_by(Sleep.created_at.desc())
        
        result = await self.db.execute(stmt)
        sleeps = result.scalars().all()
        
        data = [{
            'Nickname': s.user.nickname if s.user else 'Unknown',
            'Sleep_Time': self._localize(s.sleep_time),
            'Wake_Up_Time': self._localize(s.wake_up_time),
            'Sleep_Duration_Minutes': s.sleep_duration_minutes,
            'Target_Sleep_Hours': s.target_sleep_hours,
            'Created_At': self._localize(s.created_at)
        } for s in sleeps]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(['Nickname', 'Sleep_Time'], ascending=[True, False])
        return df

    async def get_food_habit_pivot(self):
        """Data kebiasaan makan dalam format pivot"""
        stmt = select(FoodHabitAnswer).join(User).where(
            and_(User.role != 'admin', FoodHabitAnswer.deleted_at.is_(None))
        ).options(selectinload(FoodHabitAnswer.user), selectinload(FoodHabitAnswer.question))
        
        result = await self.db.execute(stmt)
        answers = result.scalars().all()
        
        raw = []
        for a in answers:
            ans_val = 'Yes' if a.answer else 'No'
            if a.frequency: ans_val += f" ({a.frequency})"
            
            raw.append({
                'Nickname': a.user.nickname,
                'Date': self._localize(a.created_at).date(),
                'Question': a.question.question if a.question else "Unknown Q",
                'Answer': ans_val
            })
        
        df = pd.DataFrame(raw)
        if df.empty: return df
        
        pivot = df.pivot_table(index=['Nickname', 'Date'], columns='Question', 
                               values='Answer', aggfunc='last').reset_index()
        return pivot.sort_values(['Nickname', 'Date'], ascending=[True, False])

    async def get_exercise_habit_pivot(self):
        """Data kebiasaan olahraga dalam format pivot"""
        stmt = select(ExerciseHabitAnswer).join(User).where(
            and_(User.role != 'admin', ExerciseHabitAnswer.deleted_at.is_(None))
        ).options(selectinload(ExerciseHabitAnswer.user), selectinload(ExerciseHabitAnswer.question))
        
        result = await self.db.execute(stmt)
        answers = result.scalars().all()
        
        raw = []
        for a in answers:
            val = a.selected_option or a.answer_text or '-'
            rec_date = self._localize(a.recorded_at or a.created_at).date()
            
            raw.append({
                'Nickname': a.user.nickname,
                'Date': rec_date,
                'Question': a.question.question if a.question else "Unknown Q",
                'Answer': val
            })
        
        df = pd.DataFrame(raw)
        if df.empty: return df
        
        pivot = df.pivot_table(index=['Nickname', 'Date'], columns='Question', 
                               values='Answer', aggfunc='last').reset_index()
        return pivot.sort_values(['Nickname', 'Date'], ascending=[True, False])

    async def get_food_diary_data(self):
        """Data food diary harian dan detail"""
        stmt = select(FoodDiaryAnalysis).join(User).where(
            and_(User.role != 'admin', FoodDiaryAnalysis.deleted_at.is_(None))
        ).options(
            selectinload(FoodDiaryAnalysis.user),
            selectinload(FoodDiaryAnalysis.items).selectinload(FoodDiaryItem.food)
        ).order_by(FoodDiaryAnalysis.created_at.desc())
        
        result = await self.db.execute(stmt)
        analyses = result.unique().scalars().all()
        
        daily, details = [], []
        for a in analyses:
            u_name = a.user.nickname
            d_date = self._localize(a.created_at).date()
            
            daily.append({
                'Nickname': u_name, 'Date': d_date, 'Activity': a.activity,
                'Energy_Req': a.energy_requirement, 'Desired_Req': a.desired_energy_requirement,
                'Total_Cal': a.total_calories, 'Points': a.reward_points
            })
            
            for item in (a.items or []):
                details.append({
                    'Nickname': u_name, 'Date': d_date,
                    'Meal': item.meal_type.value if hasattr(item.meal_type, 'value') else item.meal_type,
                    'Food': item.food.name if item.food else 'Unknown',
                    'Qty': item.quantity, 'Grams': item.weight_grams,
                    'Cal_100g': item.food.calories if item.food else 0
                })
        
        return pd.DataFrame(daily), pd.DataFrame(details)

    def _apply_styling(self, writer, sheet_name):
        """Apply professional styling to sheets"""
        ws = writer.sheets[sheet_name]
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                        top=Side(style='thin'), bottom=Side(style='thin'))
        
        for cell in ws[1]:
            cell.fill, cell.font, cell.border = header_fill, header_font, border
            cell.alignment = Alignment(horizontal="center")

        for col in ws.columns:
            max_len = max([len(str(cell.value or "")) for cell in col])
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)
        
        ws.freeze_panes = 'A2'

    async def generate_excel(self) -> BytesIO:
        output = BytesIO()
        async with self.db.begin(): # Memastikan session aktif
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Mapping functions to sheet names
                tasks = [
                    (self.get_users_data, '1_Demographics'),
                    (self.get_nutrition_data, '2_Body_Composition'),
                    (self.get_sleep_records, '3_Sleep_Records'),
                    (self.get_food_habit_pivot, '4_Food_Habits'),
                    (self.get_exercise_habit_pivot, '5_Exercise_Habits')
                ]
                
                created = []
                for func, name in tasks:
                    df = await func()
                    if not df.empty:
                        df.to_excel(writer, sheet_name=name, index=False)
                        created.append(name)
                
                # Special handling for Food Diary (returns 2 DFs)
                df_sum, df_det = await self.get_food_diary_data()
                if not df_sum.empty:
                    df_sum.to_excel(writer, sheet_name='6_Food_Diary_Summary', index=False)
                    created.append('6_Food_Diary_Summary')
                if not df_det.empty:
                    df_det.to_excel(writer, sheet_name='7_Food_Diary_Detail', index=False)
                    created.append('7_Food_Diary_Detail')

                if not created:
                    pd.DataFrame({'Status': ['No Data']}).to_excel(writer, sheet_name='Empty')
                    created.append('Empty')

                for sn in created:
                    self._apply_styling(writer, sn)
                    
        output.seek(0)
        return output