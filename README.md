# SEHATI

SEHATI is a digital health backend for teenagers (target age 14–19) that helps track nutrition, eating habits, physical activity, sleep, and overall health status. Beyond self-monitoring, the platform also runs an engagement program (points, leaderboard, merchandise/games redemption), educational content (videos, recipes, social forum), and consultation with health professionals (doctors/psychologists) through an appointment system.

Built with FastAPI (async), PostgreSQL, and a Jinja2-based admin dashboard for content management and day-to-day operations.

---

## 1. Business Overview

SEHATI runs two product surfaces on a single backend:

| Surface | For whom | Main function |
|---|---|---|
| **Public API** (`/api/*`) | User-facing mobile/web app (teenagers) | Register & login, fill nutrition/activity questionnaires, log food/sleep/weight-height, join the forum, earn & redeem points, book consultations with professionals, chat |
| **Admin dashboard** (`/dashboard/*`) | Internal SEHATI team | Manage content (recipes, videos, games, merchandise), manage master data (foods, professionals), moderate & approve (merchandise claims, appointments), send email blasts, view leaderboard & export health data |

**Why this matters for the business:**
- **Retention & engagement** are driven by a dual-wallet point system — *achievement points* (leaderboard score, non-spendable) and *credit points* (redeemable for games/merchandise) — to keep users logging their health data regularly.
- **Clinical accuracy** is preserved through WHO-standard nutrition status calculation (BMI-for-age z-score) and Estimated Energy Requirement (EER), not a generic BMI calculator — relevant given the app's adolescent target population.
- **Professional consultation channel** (appointment) provides an escalation path from self-monitoring to a real expert, with a confirm/reject flow the professional can complete straight from an email link (no login required).

---

## 2. Architecture & Technology

- **Framework**: FastAPI (async), served via Uvicorn.
- **Database**: PostgreSQL, accessed through SQLAlchemy 2.0 (async, `asyncpg`) with schema migrations managed by Alembic (`alembic/versions/`).
- **Cache / transient state**: Redis — holds not-yet-verified registration/reset-password data (with TTL) before it's promoted to a permanent `User` row.
- **Authentication**:
  - Public API: JWT bearer tokens (`Authorization: Bearer ...`), issued by `TokenService` (`app/src/core/security.py`) with a `type` claim per purpose (`access`, `refresh`, `reset_password`, `appointment`, etc.). Passwords are hashed with Argon2.
  - Admin dashboard: the same JWT mechanism, but stored as an httponly `admin_access` cookie (not a header), plus CSRF protection (HMAC token) on every `POST` form.
- **Email**: SMTP + Jinja2 HTML templates (`app/src/templates/emails/`) — account verification, password reset, appointment notifications, merchandise claim approval/rejection, mass email blasts.
- **Real-time chat**: WebSocket (`/ws/chat`) with an in-memory connection manager; message history is persisted to the database.
- **Deployment**: GitHub Actions (`.github/workflows/deploy.yml`) triggers `deploy.sh` on the VPS on every push to `main`.

Code layout:
```
app/src/router/<domain>/api.py    → endpoints per domain
app/src/router/<domain>/crud.py   → database queries
app/src/router/<domain>/schema.py → request/response validation (Pydantic)
app/src/models/                   → table definitions (SQLAlchemy ORM)
app/src/core/                     → config, security/JWT, DB session, templates
app/src/utils/                    → cross-domain logic (nutrition calculator, point system, email, etc.)
app/src/templates/                → admin dashboard pages & email templates (Jinja2)
```

---

## 3. Points Concept (Gamification)

Each of the following activities awards points (configured via `PointCategory`, executed through `point_service.reward_user_points`):
- Daily login (1x/day)
- Filling the DQQ (Diet Quality Questionnaire) — 1x/day
- Filling the PAQ-A (Physical Activity Assessment) — 1x/day
- Submitting a food diary entry — 1x/day
- Logging a nutrition measurement (weight/height) — 1x/day
- Watching an educational video, reading a recipe — 1x per content item
- Creating a forum post, setting a reminder

Points land in two "wallets" at once: **achievement points** (permanent leaderboard score) and **credit points** (spendable balance). Credit points can be redeemed to **claim a game** or **redeem merchandise** (requires admin approval). The "already submitted today?" check is each calling endpoint's own responsibility, not `point_service`'s.

---

## 4. Endpoint Reference

All public API endpoints are prefixed with `/api` and require an `Authorization: Bearer <access_token>` header unless stated otherwise.

### 4.1 Authentication — `/api/auth`
| Method | Path | Purpose |
|---|---|---|
| POST | `/register` | Register a new account (validates age 14–19, unique email/nickname, password regex). Data is held temporarily in Redis; a 6-digit verification code is emailed (1h TTL). |
| POST | `/login` | Login with email+password, issues an `access_token` (6h) + `refresh_token` (24h), awards daily login points. |
| POST | `/refresh` | Exchange a refresh token for a new access token (12h). |
| POST | `/verify/account` | Confirm the registration code → creates the `User` row + a permanent point wallet. |
| POST | `/reset-password` | Request a password reset; emails a 6-digit code (15 min TTL) if the email exists (does not leak account existence). |
| POST | `/reset-password/confirm` | Confirm the reset code + set a new password. |

### 4.2 User Profile — `/api/users`
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Search/list other users (for chat/forum). |
| POST | `/profile/picture` | Upload a profile picture (validated by content-type + magic bytes + size limit). |
| GET | `/profile` | Own profile, including point balance & leaderboard rank. |
| GET | `/{id}` | Another user's public profile. |
| GET | `/notification/reminder` | Summary of today's incomplete tasks (questionnaires/diary/self-monitoring). |

### 4.3 Nutrition & Anthropometry — `/api/user/nutrition`
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | User's nutrition measurement history. |
| POST | `/` | Log today's weight/height → computes BMI, nutrition status (WHO z-score), ideal weight (1x/day, awards points). |
| GET | `/latest` | Latest nutrition record. |
| POST | `/calculator` | Standalone BMI/EER calculator (no persistence) — input `dob`, `gender`, `weight`, `height`, `activity`. |

### 4.4 Eating Habits / DQQ + Food Diary — `/api/habit`
| Method | Path | Purpose |
|---|---|---|
| GET | `/food` | Search the reference food/calorie database. |
| GET | `/food/questions` | Fetch the DQQ (Diet Quality Questionnaire) questions. |
| POST | `/food/answers` | Submit today's DQQ answers (1x/day, awards points). |
| POST | `/food/diary` | Submit a food diary (list of foods + portions for today) → computes total calories vs. EER (1x/day, awards points). |
| GET | `/food/diary/analysis` | History of food diary analysis records. |

### 4.5 Physical Activity / PAQ-A — `/api/exercise`
| Method | Path | Purpose |
|---|---|---|
| GET | `/questions` | Fetch the PAQ-A (Physical Activity Assessment) questions. |
| POST | `/answers` | Submit today's answers (1x/day, awards points). |

### 4.6 Sleep — `/api/sleep`
| Method | Path | Purpose |
|---|---|---|
| POST | `/` | Log a sleep session (`sleep_time`, `wake_up_time`, `target_sleep_hours`); duration is computed automatically. |
| GET | `/` | Sleep history (paginated). |

### 4.7 Reminders — `/api/reminders`
Full CRUD (`GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`) for a user's custom reminders (time, active days, message). Creating a reminder awards points.

### 4.8 Professional Appointments — `/api/appointment`
| Method | Path | Purpose |
|---|---|---|
| GET | `/professionals` | List doctors/psychologists available for booking. |
| POST | `/` | Create an appointment — validates the professional's per-day availability, awards points (nutrition counseling 1x/week, psychologist counseling 1x/month), emails the professional a confirmation link with a JWT approve/reject token. |
| GET | `/` | List the requesting user's own appointments. |
| GET | `/{appointment_id}` | Detail of one appointment. |
| GET | `/{status}/{code}` | **Public, no login required** — the link a professional clicks from email to approve/reject an appointment (`status` = `approved`/`rejected`, `code` = a single-use JWT token); sends a status email to the patient. |

### 4.9 Real-time Chat — `/ws/chat` + `/api/chat`
| Method | Path | Purpose |
|---|---|---|
| WS | `/ws/chat` | Real-time 1:1 chat. Token sent via the `Authorization` header or `?token=` query param. Send `{to, message}`, receive `{room_id, from, message, ...}`. |
| GET | `/api/chat/rooms` | List the user's chat rooms + last-message preview. |
| GET | `/api/chat/messages/{room_key}` | Message history for one room (paginated). |

### 4.10 Social Forum — `/api/forum`
| Method | Path | Purpose |
|---|---|---|
| POST | `/` | Create a post (image + caption), awards points. |
| GET | `/` | Post feed (paginated), including like/comment counts & `is_liked` status. |
| GET | `/{post_id}` | Post detail + all comments. |
| POST | `/{post_id}/like` | Toggle like. |
| POST | `/{post_id}/comment` | Add a comment. |

### 4.11 Educational Content & Rewards
| Domain | Endpoints | Purpose |
|---|---|---|
| Video — `/api/video` | `GET /`, `POST /claim-point` | List educational videos; claim watch points (1x per video). |
| Recipe — `/api/recipe` | `GET /`, `POST /claim-point` | List healthy recipes; claim read points (1x per recipe). |
| Games — `/api/games` | `GET /`, `GET /{id}/play`, `POST /{id}/claim` | List games; play (if already claimed); claim a game by spending credit points. |
| Merchandise — `/api/merchandise` | `GET /`, `POST /claim` | List merchandise; submit a claim (pending admin approval) by spending credit points. |
| Leaderboard — `/api/point` | `GET /leaderboard` | Rank all users by achievement points. |

### 4.12 Admin Dashboard — `/dashboard`
Cookie-session authentication (`admin_access`), not bearer tokens. Every `POST` form is protected by a CSRF token.

| Area | Main endpoints | Purpose |
|---|---|---|
| Login | `GET/POST /login`, `POST /logout` | Admin login & session management. |
| Users | `GET /users`, `GET /users/{id}`, `POST /users/{id}/delete`, `GET/POST /reset/password[/confirm]` | Manage & moderate user accounts, reset a user's password on their behalf. |
| Recipes | `GET /recipes`, `GET/POST /recipes/upload` | Manage recipe content. |
| Videos | `GET /videos`, `GET/POST /videos/create`, `POST /videos/delete/{id}`, `POST /videos/toggle/{id}` | Manage educational video content + active/inactive status. |
| Games | `GET /games`, `GET/POST /games/create`, `GET /games/{id}/view` | Manage the games catalog. |
| Foods | `GET /foods`, `GET/POST /foods/create`, `POST /foods/update/{id}`, `POST /foods/delete/{id}` | Manage the reference food/calorie database. |
| Merchandise | `GET/POST /merchandise/upload`, `GET /merchandise`, `POST /merchandise/update/{id}`, `GET /merchandise/claims`, `POST /merchandise/claims/{id}/approve|reject` | Manage the merchandise catalog & approve redemption claims. |
| Professionals | `GET /professionals`, `GET/POST /professionals/create`, `GET /professionals/{id}/edit`, `POST /professionals/{id}/update|delete` | Manage doctor/psychologist records including per-day availability schedules. |
| Appointments | `GET /appointments`, `POST /appointments/update/{id}/{status}`, `POST /appointments/delete/{id}` | In-dashboard alternative to confirm/reject/delete appointments (besides the email flow). |
| Point Transactions | `GET /transactions`, `GET /transactions/export` | View & export (Excel) the point transaction ledger. |
| Leaderboard | `GET /leaderboard` | View the point ranking of all users. |
| Health Data Export | `GET /export/health-data` | Bulk export of users' nutrition/health records to Excel. |
| Email Blast | `GET/POST /blast`, `GET /blast/{id}/detail`, `GET /api/blast/{id}/status`, `POST /blast/{id}/retry` | Send mass email to user segments, track send progress, retry failed sends. |

### 4.13 Other Public Pages
- `GET /` → redirects to `/dashboard/login`.
- `GET /privacy-policy`, `GET /term-of-service` → static policy pages (Jinja2).

---

## 5. Core Data Modules (Models)

| Model | Business meaning |
|---|---|
| `user.py` | User account/profile — the central entity most other domain data hangs off of, with a role flag (user/admin). |
| `user_nutrition.py` | A point-in-time body measurement snapshot (height/weight/BMI/status/ideal weight). |
| `bmi_reference.py` | WHO BMI-for-age standard-deviation reference table per gender/age, the basis for the nutrition z-score calculation. |
| `food.py` | Reference food/calorie database, DQQ questionnaire, and daily food diary entries. |
| `exercise_habit.py` | PAQ-A questionnaire and users' daily answers. |
| `sleep.py` | A logged sleep session (sleep/wake time, duration, target). |
| `reminder.py` | A user's recurring reminder (time, active days, message). |
| `point.py` | The gamification system — point categories, each user's dual wallet (achievement/credit), and the transaction ledger. |
| `games.py` | Catalog of point-claimable games + each user's claim status. |
| `merchandise.py` | Catalog of point-redeemable physical merchandise + claim status (pending/approved/rejected). |
| `recipe.py` | Healthy recipe content + records of the "read a recipe" point claim. |
| `video.py` | Educational video catalog + records of the "watch video" point claim. |
| `forum.py` | Social forum posts (image + caption) with their likes and comments. |
| `chat.py` | 1:1 chat rooms, their participants, and message history. |
| `professionals.py` | Doctor/psychologist records (including availability schedule) and the appointments users book with them. |
| `blast_log.py` | Log of a mass email blast (subject/body/recipients/send results) sent by an admin. |

---

## 6. Key Business Logic

**Nutrition Calculator** (`app/src/utils/nutrition_calculator.py`)
Computes BMI from weight/height, matches it against the `BMIReference` table (WHO standard deviations) based on the user's exact age (years + months) with interpolation between adjacent age bands, then classifies nutrition status (Severely Underweight/Underweight/Normal/Overweight/Obese). Also computes ideal body weight (Broca formula — 10% deduction for males, 15% for females) and Estimated Energy Requirement (EER) using IOM/DRI equations with gender-specific physical-activity coefficients. **Capped at age 19 years 0 months** — matching the app's teen target population; raises an error beyond that.

**Point System** (`app/src/utils/point_service.py`)
`reward_user_points` looks up the point value from `PointCategory` and credits both wallets at once (achievement + credit) with one transaction row per wallet. `redeem_merchandise_points`/`claim_games` are the reverse flow: check sufficient credit balance, debit, log the transaction. The "already claimed/submitted today" check is each calling endpoint's responsibility, not this service's.

---

## 7. Running Locally

```bash
poetry install
# create a .env file with DATABASE_URL, REDIS_*, SMTP_*, SECRET_KEY, etc. — see app/src/core/config.py
alembic upgrade head
uvicorn main:app --reload
```

Required environment variables (see `app/src/core/config.py`): `SECRET_KEY`, `DATABASE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SENDER`. Redis (`REDIS_HOST`/`REDIS_PORT`) holds transient registration/reset-password state.

Interactive API docs are automatically available at `/docs` (Swagger UI) while the server is running.

## 8. Deployment

A push to the `main` branch triggers GitHub Actions (`.github/workflows/deploy.yml`), which SSHes into the VPS and runs `deploy.sh`.
