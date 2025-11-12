from datetime import date
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.bmi_reference import BMIReference

class NutritionCalculator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_reference(self, gender: str, years: int, months: int):
        query = select(BMIReference).where(
            BMIReference.gender == gender,
            BMIReference.age_years == years,
            BMIReference.age_months == months
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def calculate_bmi(self, weight: float, height: float):
        return round(weight / ((height / 100) ** 2), 1)

    def calculate_ibw(self, height: float, method: str = "devine", gender: str = "male"):
        if method == "devine":
            if gender == "male":
                return round(50 + 0.9 * (height - 152.4), 1)
            return round(45.5 + 0.9 * (height - 152.4), 1)
        if gender == "male":
            return round((height - 100) - (height - 100) * 0.1, 1)
        return round((height - 100) - (height - 100) * 0.15, 1)

    def calculate_zscore(self, bmi: float, ref: BMIReference):
        if not ref:
            return None
        values = {
            -3: float(ref.sd_minus_3),
            -2: float(ref.sd_minus_2),
            -1: float(ref.sd_minus_1),
             0: float(ref.median),
             1: float(ref.sd_plus_1),
             2: float(ref.sd_plus_2),
             3: float(ref.sd_plus_3),
        }
        sorted_keys = sorted(values.keys())
        for i in range(len(sorted_keys) - 1):
            low, high = sorted_keys[i], sorted_keys[i + 1]
            if values[low] <= bmi <= values[high]:
                ratio = (bmi - values[low]) / (values[high] - values[low])
                return round(low + ratio * (high - low), 2)
        if bmi < values[-3]:
            return -3
        if bmi > values[3]:
            return 3
        return 0

    def classify_status(self, zscore: float):
        if zscore < -3:
            return "Severely Underweight"
        if -3 <= zscore < -2:
            return "Underweight"
        if -2 <= zscore <= 1:
            return "Normal"
        if 1 < zscore <= 2:
            return "Overweight"
        return "Obese"

    async def evaluate(self, gender: str, dob: date, weight: float, height: float, ref_date: date = date.today(), activity: str = None):
        years = ref_date.year - dob.year
        months = ref_date.month - dob.month
        if years > 19 or (years==19 and months > 0):
            raise ValueError(f"You are {years} years and {months} months old. This calculator only supports up to 19 years and 0 months."
)
        if months < 0:
            years -= 1
            months += 12
        ref = await self.get_reference(gender, years, months)
        bmi = self.calculate_bmi(weight, height)
        zscore = self.calculate_zscore(bmi, ref)
        status = self.classify_status(zscore)
        ibw = self.calculate_ibw(height, gender=gender)
        eer = 0 if not activity else self.calculate_eer(gender=gender, age=years, weight=weight, height=height, activity=activity)
        return {"bmi": bmi, "zscore": zscore, "status": status, "ibw": ibw, "eer":eer}

    def calculate_eer(self, gender: str, age: int, weight: float, height: float, activity: str):
        pa_values = {
            "sedentary": 1.0,
            "low_active": 1.11 if gender.lower() == "male" else 1.12,
            "active": 1.25 if gender.lower() == "male" else 1.27,
            "very_active": 1.48 if gender.lower() == "male" else 1.45,
        }
        pa = pa_values.get(activity, 1.0)
        h_m = height / 100
        if gender.lower() == "male":
            eer = 662 - (9.53 * age) + pa * ((15.91 * weight) + (539.6 * h_m))
        else:
            eer = 354 - (6.91 * age) + pa * ((9.36 * weight) + (726 * h_m))
        return round(eer, 1)