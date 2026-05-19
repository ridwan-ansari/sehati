from __future__ import annotations
from fastapi import Header

MESSAGES: dict[str, dict[str, str]] = {
    # ── Auth ──────────────────────────────────────────────────────────────
    "email_already_registered": {
        "en": "Email is already registered. Please use another email.",
        "id": "Email sudah terdaftar. Silakan gunakan email lain.",
    },
    "nickname_already_registered": {
        "en": "Nickname is already registered. Please use another nickname.",
        "id": "Nickname sudah terdaftar. Silakan gunakan nickname lain.",
    },
    "picture_format_wrong": {
        "en": "The picture format is invalid, please check again.",
        "id": "Format gambar tidak valid, silakan periksa kembali.",
    },
    "password_invalid": {
        "en": "Password must be at least 8 characters containing only letters and numbers.",
        "id": "Password minimal 8 karakter dan hanya boleh mengandung huruf dan angka.",
    },
    "age_too_young": {
        "en": "Minimum age to register is 14 years old.",
        "id": "Usia minimal untuk mendaftar adalah 14 tahun.",
    },
    "age_too_old": {
        "en": "Maximum allowed age is 19 years old.",
        "id": "Usia maksimal yang diizinkan adalah 19 tahun.",
    },
    "something_went_wrong": {
        "en": "Something went wrong. Please try again later.",
        "id": "Terjadi kesalahan. Silakan coba lagi nanti.",
    },
    "register_success": {
        "en": "Account registered successfully.",
        "id": "Akun berhasil didaftarkan.",
    },
    "login_invalid": {
        "en": "Your email or password is incorrect. Please check and try again.",
        "id": "Email atau password Anda salah. Silakan periksa dan coba lagi.",
    },
    "login_success": {
        "en": "Successfully logged in.",
        "id": "Berhasil masuk.",
    },
    "token_invalid": {
        "en": "Invalid or expired token.",
        "id": "Token tidak valid atau sudah kedaluwarsa.",
    },
    "token_expired": {
        "en": "Token has expired.",
        "id": "Token sudah kedaluwarsa.",
    },
    "token_malformed": {
        "en": "Invalid token.",
        "id": "Token tidak valid.",
    },
    "token_validation_failed": {
        "en": "Token validation failed: {error}",
        "id": "Validasi token gagal: {error}",
    },
    "access_token_invalid": {
        "en": "Invalid access token.",
        "id": "Token akses tidak valid.",
    },
    "refresh_token_invalid": {
        "en": "Invalid refresh token.",
        "id": "Token refresh tidak valid.",
    },
    "admin_access_required": {
        "en": "Admin access required.",
        "id": "Akses admin diperlukan.",
    },
    "verification_code_invalid": {
        "en": "Invalid verification code. Please enter the correct one and try again.",
        "id": "Kode verifikasi tidak valid. Silakan masukkan kode yang benar dan coba lagi.",
    },
    "account_verified": {
        "en": "Your account has been successfully verified. Please log in to continue.",
        "id": "Akun Anda telah berhasil diverifikasi. Silakan masuk untuk melanjutkan.",
    },
    "reset_password_sent": {
        "en": "Please check your email. If your account exists, you will receive a verification code.",
        "id": "Silakan periksa email Anda. Jika akun terdaftar, Anda akan menerima kode verifikasi.",
    },
    "passwords_not_match": {
        "en": "Passwords do not match.",
        "id": "Password tidak cocok.",
    },
    "reset_code_invalid": {
        "en": "Invalid verification code or the code has expired.",
        "id": "Kode verifikasi tidak valid atau sudah kedaluwarsa.",
    },
    "password_reset_success": {
        "en": "Password has been reset successfully. Please log in using your new password.",
        "id": "Password berhasil diatur ulang. Silakan masuk menggunakan password baru Anda.",
    },

    # ── User ──────────────────────────────────────────────────────────────
    "user_list_success": {
        "en": "User list retrieved successfully.",
        "id": "Daftar pengguna berhasil diambil.",
    },
    "image_only_allowed": {
        "en": "Only image files are allowed.",
        "id": "Hanya file gambar yang diizinkan.",
    },
    "profile_picture_updated": {
        "en": "Profile picture updated successfully.",
        "id": "Foto profil berhasil diperbarui.",
    },
    "profile_success": {
        "en": "Profile retrieved successfully.",
        "id": "Profil berhasil diambil.",
    },
    "user_success": {
        "en": "User retrieved successfully.",
        "id": "Data pengguna berhasil diambil.",
    },
    "all_tasks_complete": {
        "en": "Great job! You've completed all your tasks for today.",
        "id": "Kerja bagus! Anda telah menyelesaikan semua tugas hari ini.",
    },
    "incomplete_tasks": {
        "en": "You haven't completed your {tasks} today.",
        "id": "Anda belum menyelesaikan {tasks} hari ini.",
    },
    "notification_success": {
        "en": "Notification reminder retrieved successfully.",
        "id": "Pengingat notifikasi berhasil diambil.",
    },

    # Task names (used inside notification messages)
    "task_exercise_habit": {"en": "Exercise Habit",  "id": "Kebiasaan Olahraga"},
    "task_food_habit":     {"en": "Food Habit",      "id": "Kebiasaan Makan"},
    "task_food_diary":     {"en": "Food Diary",      "id": "Diary Makanan"},
    "task_self_monitoring":{"en": "Self Monitoring", "id": "Self Monitoring"},
    "conjunction_and":     {"en": "and",             "id": "dan"},

    # ── Food ──────────────────────────────────────────────────────────────
    "food_list_success": {
        "en": "Food list retrieved successfully.",
        "id": "Daftar makanan berhasil diambil.",
    },
    "food_questions_success": {
        "en": "Food habit questions retrieved successfully.",
        "id": "Pertanyaan kebiasaan makan berhasil diambil.",
    },
    "already_submitted_today": {
        "en": "Your submission has been received today. Please submit again tomorrow.",
        "id": "Data Anda hari ini sudah diterima. Silakan isi kembali besok.",
    },
    "food_answers_success": {
        "en": "Food habit answers submitted successfully.",
        "id": "Jawaban kebiasaan makan berhasil dikirim.",
    },
    "food_diary_success": {
        "en": "Food diary submitted successfully.",
        "id": "Diary makanan berhasil dikirim.",
    },
    "diary_retrieved_success": {
        "en": "Diary retrieved successfully.",
        "id": "Diary berhasil diambil.",
    },

    # ── Games ─────────────────────────────────────────────────────────────
    "games_list_success": {
        "en": "Games retrieved successfully.",
        "id": "Daftar permainan berhasil diambil.",
    },
    "contact_admin": {
        "en": "Something went wrong. Please contact the administrator.",
        "id": "Terjadi kesalahan. Silakan hubungi administrator.",
    },
    "game_not_found": {
        "en": "Game not found.",
        "id": "Permainan tidak ditemukan.",
    },
    "game_claimed_success": {
        "en": "Congratulations, the game has been claimed.",
        "id": "Selamat, permainan berhasil diklaim.",
    },

    # ── Merchandise ───────────────────────────────────────────────────────
    "merchandise_list_success": {
        "en": "Merchandise retrieved successfully.",
        "id": "Daftar merchandise berhasil diambil.",
    },
    "insufficient_points": {
        "en": "Transaction failed: Insufficient points.",
        "id": "Transaksi gagal: Poin tidak mencukupi.",
    },
    "claim_sent_to_admin": {
        "en": "Your claim has been submitted. Once approved, you will receive an email.",
        "id": "Klaim Anda telah dikirim. Setelah disetujui, Anda akan menerima email.",
    },
    "merchandise_not_found": {
        "en": "Merchandise not found.",
        "id": "Merchandise tidak ditemukan.",
    },
    "merchandise_inactive": {
        "en": "Merchandise is not active.",
        "id": "Merchandise tidak aktif.",
    },
    "merchandise_insufficient_stock": {
        "en": "Insufficient stock. Available: {stock}.",
        "id": "Stok tidak mencukupi. Tersedia: {stock}.",
    },
    "merchandise_already_claimed": {
        "en": "You have already claimed this merchandise.",
        "id": "Anda sudah mengklaim merchandise ini.",
    },
    "merchandise_claim_pending": {
        "en": "You already have a pending claim for this merchandise.",
        "id": "Anda sudah memiliki klaim merchandise ini yang sedang menunggu persetujuan.",
    },

    # ── Video ─────────────────────────────────────────────────────────────
    "video_list_success": {
        "en": "Video list retrieved successfully.",
        "id": "Daftar video berhasil diambil.",
    },
    "video_not_found": {
        "en": "Video not found.",
        "id": "Video tidak ditemukan.",
    },
    "reward_claimed_success": {
        "en": "Reward claimed successfully.",
        "id": "Hadiah berhasil diklaim.",
    },

    # ── Recipe ────────────────────────────────────────────────────────────
    "recipe_list_success": {
        "en": "Recipe list retrieved successfully.",
        "id": "Daftar resep berhasil diambil.",
    },
    "recipe_not_found": {
        "en": "Recipe not found.",
        "id": "Resep tidak ditemukan.",
    },

    # ── Appointment ───────────────────────────────────────────────────────
    "professionals_fetched": {
        "en": "Professionals retrieved successfully.",
        "id": "Daftar profesional berhasil diambil.",
    },
    "doctor_not_found": {
        "en": "Doctor not found.",
        "id": "Dokter tidak ditemukan.",
    },
    "appointment_created": {
        "en": "Appointment created successfully.",
        "id": "Janji temu berhasil dibuat.",
    },
    "appointments_fetched": {
        "en": "Appointments retrieved successfully.",
        "id": "Daftar janji temu berhasil diambil.",
    },
    "appointment_detail": {
        "en": "Appointment detail retrieved successfully.",
        "id": "Detail janji temu berhasil diambil.",
    },
    "professional_not_available_on_day": {
        "en": "The professional is not available on {day}.",
        "id": "Profesional tidak tersedia pada hari {day}.",
    },
    "professional_schedule_unset": {
        "en": "The professional has not set their availability schedule yet.",
        "id": "Profesional belum mengatur jadwal ketersediaan.",
    },
    "appointment_time_outside_hours": {
        "en": "Selected time is outside available hours ({start} - {end}).",
        "id": "Waktu yang dipilih di luar jam tersedia ({start} - {end}).",
    },
    "day_monday":    {"en": "Monday",    "id": "Senin"},
    "day_tuesday":   {"en": "Tuesday",   "id": "Selasa"},
    "day_wednesday": {"en": "Wednesday", "id": "Rabu"},
    "day_thursday":  {"en": "Thursday",  "id": "Kamis"},
    "day_friday":    {"en": "Friday",    "id": "Jumat"},
    "day_saturday":  {"en": "Saturday",  "id": "Sabtu"},
    "day_sunday":    {"en": "Sunday",    "id": "Minggu"},

    # ── Forum ─────────────────────────────────────────────────────────────
    "post_created": {
        "en": "Post created successfully.",
        "id": "Postingan berhasil dibuat.",
    },
    "like_updated": {
        "en": "Like status updated.",
        "id": "Status suka berhasil diperbarui.",
    },
    "comment_added": {
        "en": "Comment added successfully.",
        "id": "Komentar berhasil ditambahkan.",
    },
    "posts_fetched": {
        "en": "Posts retrieved successfully.",
        "id": "Daftar postingan berhasil diambil.",
    },
    "post_detail_fetched": {
        "en": "Post detail retrieved successfully.",
        "id": "Detail postingan berhasil diambil.",
    },

    # ── Point ─────────────────────────────────────────────────────────────
    "leaderboard_success": {
        "en": "Leaderboard retrieved successfully.",
        "id": "Papan peringkat berhasil diambil.",
    },
    "insufficient_credit_points": {
        "en": "Transaction failed: Insufficient credit points.",
        "id": "Transaksi gagal: Kredit poin tidak mencukupi.",
    },
    "point_category_not_found": {
        "en": "Point category configuration not found. Please contact the administrator.",
        "id": "Konfigurasi kategori poin tidak ditemukan. Silakan hubungi administrator.",
    },

    # ── Chat ──────────────────────────────────────────────────────────────
    "chat_invalid_format": {
        "en": "Invalid message format. Required fields: to, message.",
        "id": "Format pesan tidak valid. Field wajib: to, message.",
    },
    "messages_success": {
        "en": "Messages retrieved successfully.",
        "id": "Pesan berhasil diambil.",
    },
    "rooms_success": {
        "en": "Chat rooms retrieved successfully.",
        "id": "Daftar ruang obrolan berhasil diambil.",
    },

    # ── Sleep ─────────────────────────────────────────────────────────────
    "sleep_time_invalid": {
        "en": "Wake up time must be after sleep time.",
        "id": "Waktu bangun harus setelah waktu tidur.",
    },
    "sleep_date_invalid": {
        "en": "Sleep time must be yesterday or today.",
        "id": "Waktu tidur harus kemarin atau hari ini.",
    },
    "wake_up_date_invalid": {
        "en": "Wake up time must be today.",
        "id": "Waktu bangun harus hari ini.",
    },
    "sleep_already_submitted_today": {
        "en": "You have already submitted a sleep record today.",
        "id": "Anda sudah menyimpan catatan tidur hari ini.",
    },
    "sleep_created_success": {
        "en": "Sleep record created successfully.",
        "id": "Catatan tidur berhasil disimpan.",
    },
    "sleep_list_success": {
        "en": "Sleep records retrieved successfully.",
        "id": "Daftar catatan tidur berhasil diambil.",
    },

    # ── Reminder ──────────────────────────────────────────────────────────
    "reminders_fetched": {
        "en": "Reminders retrieved successfully.",
        "id": "Daftar pengingat berhasil diambil.",
    },
    "reminder_created": {
        "en": "Reminder created successfully.",
        "id": "Pengingat berhasil dibuat.",
    },
    "reminder_not_found": {
        "en": "Reminder not found.",
        "id": "Pengingat tidak ditemukan.",
    },
    "reminder_retrieved": {
        "en": "Reminder retrieved successfully.",
        "id": "Pengingat berhasil diambil.",
    },
    "reminder_updated": {
        "en": "Reminder updated successfully.",
        "id": "Pengingat berhasil diperbarui.",
    },
    "reminder_deleted": {
        "en": "Reminder deleted successfully.",
        "id": "Pengingat berhasil dihapus.",
    },

    # ── Exercise ──────────────────────────────────────────────────────────
    "exercise_questions_success": {
        "en": "Exercise habit questions retrieved successfully.",
        "id": "Pertanyaan kebiasaan olahraga berhasil diambil.",
    },
    "exercise_answers_success": {
        "en": "Exercise habit answers submitted successfully.",
        "id": "Jawaban kebiasaan olahraga berhasil dikirim.",
    },

    # ── User Nutrition ────────────────────────────────────────────────────
    "nutrition_list_success": {
        "en": "Nutrition records retrieved successfully.",
        "id": "Data nutrisi berhasil diambil.",
    },
    "nutrition_created_success": {
        "en": "Nutrition record created successfully.",
        "id": "Data nutrisi berhasil disimpan.",
    },
    "nutrition_latest_success": {
        "en": "Latest nutrition data retrieved successfully.",
        "id": "Data nutrisi terbaru berhasil diambil.",
    },
    "calculation_success": {
        "en": "Calculation completed successfully.",
        "id": "Perhitungan berhasil diselesaikan.",
    },
}


def t(key: str, lang: str = "en", **kwargs: str) -> str:
    """Return the translated message for *key* in *lang*, falling back to English."""
    translations = MESSAGES.get(key, {})
    msg = translations.get(lang) or translations.get("en", key)
    return msg.format(**kwargs) if kwargs else msg


def get_lang(accept_language: str = Header(default="en")) -> str:
    """FastAPI dependency — reads Accept-Language header, returns 'en' or 'id'."""
    primary = accept_language.split(",")[0].split(";")[0].split("-")[0].strip().lower()
    return primary if primary in ("en", "id") else "en"
