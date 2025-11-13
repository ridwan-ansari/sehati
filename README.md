#SEHATI
SEHATI is a modular backend platform built with FastAPI, designed to help users monitor nutrition, eating habits, physical activity, and overall health status. It integrates scoring, habit tracking, nutrition analytics, and educational content into a unified health monitoring system.

-----------------------------------------------------
##PROJECT OVERVIEW
-----------------------------------------------------
SEHATI provides a comprehensive backend architecture that supports:
- Nutritional monitoring and evaluation
- Diet Quality Questionnaire (DQQ)
- Physical Activity Assessment (PAQ-A)
- Calorie tracking and food diary
- Automated Energy Requirement Calculation (EER)
- Reward point system
- Educational video modules
- Secure user authentication and profile management
It is designed to support adolescent and adult health programs focusing on diet quality, physical activity, and lifestyle improvement.

-----------------------------------------------------
##CORE TECHNOLOGIES
-----------------------------------------------------
- FastAPI (asynchronous backend framework)
- PostgreSQL with SQLAlchemy Async ORM
- Alembic for database migrations
- JWT Authentication + Cookie-based Admin Session
- SMTP Email Service with HTML templates
- Nginx Reverse Proxy, HTTPS (Let’s Encrypt)
- Secure Media Storage for avatar and static files
- TailwindCSS + Jinja2 for admin dashboard rendering

-----------------------------------------------------
##KEY FEATURES
-----------------------------------------------------

USER & AUTHENTICATION MODULE
- User registration, login, email verification, OTP and link-based password reset
- Role-based access (Admin / User)
- Secure avatar upload with file validation and Nginx-protected media routes

##NUTRITION & FOOD DIARY
- Daily food diary submission with total calorie calculation
- Integrated NutritionCalculator:
  - BMI, Z-Score, IBW (Broca/Devine)
  - Age- and sex-based BMI references
  - EER (Estimated Energy Requirement) & Desired Intake
- Automatic reward points for diary completion

##DIET QUALITY QUESTIONNAIRE (DQQ)
- Structured food habit questions categorized by food types
- Stored in food_habit_questions
- User answers stored in food_habit_answers
- Reward points system included

##PHYSICAL ACTIVITY ASSESSMENT (PAQ-A)
- Complete PAQ-A questionnaire modeled into exercise_habit_questions and exercise_habit_answers
- Supports multiple-choice and open-response items
- Endpoints:
  - GET /exercise/questions
  - POST /exercise/answers

##POINT & REWARD SYSTEM
- Automatic point assignment for:
  - Daily login
  - Food diary submission
  - Watching educational videos
  - Completing DQQ or PAQ-A
- Wallet and transaction tracking

##EDUCATIONAL VIDEO MODULE
- Video catalog with reward points
- Admin-configurable content
- Linked with user activities
