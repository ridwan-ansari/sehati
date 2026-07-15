# SEHATI

SEHATI adalah backend platform kesehatan digital untuk remaja (target usia 14–19 tahun) yang membantu memantau gizi, kebiasaan makan, aktivitas fisik, tidur, dan kondisi kesehatan secara umum. Selain sisi self-monitoring, platform ini juga menyediakan program engagement (poin, leaderboard, redeem merchandise/games), konten edukasi (video, resep, forum sosial), serta layanan konsultasi dengan tenaga profesional (dokter/psikolog) lewat sistem janji temu (appointment).

Dibangun dengan FastAPI (async), PostgreSQL, dan dashboard admin berbasis Jinja2 untuk pengelolaan konten dan operasional harian.

---

## 1. Gambaran Bisnis

SEHATI menjalankan dua sisi produk dalam satu backend:

| Sisi | Untuk siapa | Fungsi utama |
|---|---|---|
| **API publik** (`/api/*`) | Aplikasi mobile/web pengguna (remaja) | Registrasi & login, isi kuesioner gizi/aktivitas, catat makanan/tidur/berat-tinggi, ikut forum, kumpulkan & tukar poin, booking konsultasi dengan profesional, chat |
| **Dashboard admin** (`/dashboard/*`) | Tim internal/admin SEHATI | Kelola konten (resep, video, game, merchandise), kelola data master (makanan, profesional), moderasi & approval (klaim merchandise, appointment), kirim email blast, lihat leaderboard & ekspor data kesehatan |

**Mengapa ini penting secara bisnis:**
- **Retensi & engagement** didorong lewat sistem poin ganda — *achievement points* (untuk leaderboard, tidak bisa dibelanjakan) dan *credit points* (bisa ditukar game/merchandise) — supaya user rutin mengisi data kesehatan hariannya.
- **Kepatuhan medis** dijaga lewat kalkulasi status gizi standar WHO (BMI-for-age z-score) dan estimasi kebutuhan energi (EER), bukan sekadar kalkulator BMI generik — relevan untuk populasi remaja yang jadi target aplikasi.
- **Kanal konsultasi profesional** (appointment) memberi jalur eskalasi dari self-monitoring ke tenaga ahli sungguhan, dengan alur konfirmasi/penolakan yang bisa dilakukan profesional langsung dari email (tanpa perlu login).

---

## 2. Arsitektur & Teknologi

- **Framework**: FastAPI (async), disajikan lewat Uvicorn.
- **Database**: PostgreSQL, diakses lewat SQLAlchemy 2.0 (async, `asyncpg`) + migrasi skema dengan Alembic (`alembic/versions/`).
- **Cache/state sementara**: Redis — dipakai untuk menyimpan data registrasi/reset-password yang belum terverifikasi (dengan TTL), sebelum dipindah ke tabel `User` permanen.
- **Autentikasi**:
  - API publik: JWT bearer token (`Authorization: Bearer ...`), diterbitkan oleh `TokenService` (`app/src/core/security.py`) dengan klaim `type` per keperluan (`access`, `refresh`, `reset_password`, `appointment`, dst). Password di-hash dengan Argon2.
  - Dashboard admin: JWT yang sama tapi disimpan sebagai cookie httponly `admin_access` (bukan header), plus proteksi CSRF (HMAC token) untuk semua form `POST`.
- **Email**: SMTP + template HTML Jinja2 (`app/src/templates/emails/`) — verifikasi akun, reset password, notifikasi appointment, approval/rejection klaim merchandise, email blast massal.
- **Real-time chat**: WebSocket (`/ws/chat`) dengan connection manager in-memory, riwayat pesan tetap tersimpan di database.
- **Deploy**: GitHub Actions (`.github/workflows/deploy.yml`) memicu `deploy.sh` di VPS setiap push ke `main`.

Struktur kode:
```
app/src/router/<domain>/api.py    → endpoint per domain
app/src/router/<domain>/crud.py   → query database
app/src/router/<domain>/schema.py → validasi request/response (Pydantic)
app/src/models/                   → definisi tabel (SQLAlchemy ORM)
app/src/core/                     → config, security/JWT, DB session, templates
app/src/utils/                    → logic lintas-domain (kalkulator gizi, sistem poin, email, dll)
app/src/templates/                → halaman dashboard admin & template email (Jinja2)
```

---

## 3. Konsep Poin (Gamifikasi)

Setiap aktivitas berikut memberi poin (dikonfigurasi lewat `PointCategory`, dieksekusi lewat `point_service.reward_user_points`):
- Login harian (1x/hari)
- Mengisi kuesioner DQQ (Diet Quality Questionnaire) — 1x/hari
- Mengisi kuesioner PAQ-A (Physical Activity Assessment) — 1x/hari
- Mengisi food diary — 1x/hari
- Mencatat pengukuran gizi (berat/tinggi) — 1x/hari
- Menonton video edukasi, membaca resep — 1x per konten
- Membuat post forum, memasang reminder

Poin masuk ke dua "dompet" sekaligus: **achievement points** (skor leaderboard, permanen) dan **credit points** (saldo yang bisa dibelanjakan). Credit points bisa ditukar untuk **klaim game** atau **redeem merchandise** (butuh approval admin). Pengecekan "sudah submit hari ini?" dilakukan di masing-masing endpoint pemanggil, bukan di `point_service` itu sendiri.

---

## 4. Referensi Endpoint

Semua endpoint API publik berprefix `/api` dan butuh header `Authorization: Bearer <access_token>` kecuali disebutkan lain.

### 4.1 Autentikasi — `/api/auth`
| Method | Path | Fungsi |
|---|---|---|
| POST | `/register` | Daftar akun baru (validasi usia 14–19, email/nickname unik, regex password). Data disimpan sementara di Redis, kode verifikasi 6 digit dikirim via email (TTL 1 jam). |
| POST | `/login` | Login email+password, terbitkan `access_token` (6 jam) + `refresh_token` (24 jam), beri poin login harian. |
| POST | `/refresh` | Tukar refresh token → access token baru (12 jam). |
| POST | `/verify/account` | Konfirmasi kode registrasi → buat baris `User` + wallet poin permanen. |
| POST | `/reset-password` | Minta reset password, kirim kode 6 digit (TTL 15 menit) bila email terdaftar (tidak membocorkan status keberadaan akun). |
| POST | `/reset-password/confirm` | Konfirmasi kode + set password baru. |

### 4.2 Profil Pengguna — `/api/users`
| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Cari/list pengguna lain (untuk chat/forum). |
| POST | `/profile/picture` | Upload foto profil (divalidasi content-type + magic bytes + batas ukuran). |
| GET | `/profile` | Profil sendiri, termasuk saldo poin & ranking leaderboard. |
| GET | `/{id}` | Profil publik pengguna lain. |
| GET | `/notification/reminder` | Ringkasan tugas harian yang belum diselesaikan (kuesioner/diary/self-monitoring). |

### 4.3 Gizi & Antropometri — `/api/user/nutrition`
| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Riwayat pengukuran gizi pengguna. |
| POST | `/` | Catat berat/tinggi hari ini → hitung BMI, status gizi (z-score WHO), berat ideal (1x/hari, beri poin). |
| GET | `/latest` | Pengukuran terakhir. |
| POST | `/calculator` | Kalkulator BMI/EER berdiri sendiri (tanpa disimpan) — input `dob`, `gender`, `weight`, `height`, `activity`. |

### 4.4 Kebiasaan Makan / DQQ + Food Diary — `/api/habit`
| Method | Path | Fungsi |
|---|---|---|
| GET | `/food` | Cari makanan di database referensi kalori. |
| GET | `/food/questions` | Ambil pertanyaan kuesioner DQQ (Diet Quality Questionnaire). |
| POST | `/food/answers` | Submit jawaban DQQ hari ini (1x/hari, beri poin). |
| POST | `/food/diary` | Submit food diary (daftar makanan + porsi hari ini) → hitung total kalori vs EER (1x/hari, beri poin). |
| GET | `/food/diary/analysis` | Riwayat analisis food diary. |

### 4.5 Aktivitas Fisik / PAQ-A — `/api/exercise`
| Method | Path | Fungsi |
|---|---|---|
| GET | `/questions` | Ambil pertanyaan kuesioner PAQ-A (Physical Activity Assessment). |
| POST | `/answers` | Submit jawaban hari ini (1x/hari, beri poin). |

### 4.6 Tidur — `/api/sleep`
| Method | Path | Fungsi |
|---|---|---|
| POST | `/` | Catat sesi tidur (`sleep_time`, `wake_up_time`, `target_sleep_hours`); durasi dihitung otomatis. |
| GET | `/` | Riwayat tidur (paginasi). |

### 4.7 Pengingat — `/api/reminders`
CRUD penuh (`GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`) untuk reminder custom milik user (jam, hari aktif, pesan). Pembuatan reminder memberi poin.

### 4.8 Janji Temu Profesional — `/api/appointment`
| Method | Path | Fungsi |
|---|---|---|
| GET | `/professionals` | List dokter/psikolog yang tersedia untuk booking. |
| POST | `/` | Buat janji temu — validasi jadwal ketersediaan profesional per hari, beri poin (konseling gizi 1x/minggu, psikolog 1x/bulan), kirim email konfirmasi ke profesional berisi tautan approve/reject bertoken JWT. |
| GET | `/` | List appointment milik user sendiri. |
| GET | `/{appointment_id}` | Detail satu appointment. |
| GET | `/{status}/{code}` | **Publik, tanpa login** — tautan dari email yang diklik profesional untuk approve/reject appointment (`status` = `approved`/`rejected`, `code` = token JWT sekali pakai); mengirim email status ke pasien. |

### 4.9 Chat Real-time — `/ws/chat` + `/api/chat`
| Method | Path | Fungsi |
|---|---|---|
| WS | `/ws/chat` | Chat 1:1 real-time. Token dikirim via header `Authorization` atau query `?token=`. Kirim `{to, message}`, diterima sebagai `{room_id, from, message, ...}`. |
| GET | `/api/chat/rooms` | List room chat milik user + preview pesan terakhir. |
| GET | `/api/chat/messages/{room_key}` | Riwayat pesan dalam satu room (paginasi). |

### 4.10 Forum Sosial — `/api/forum`
| Method | Path | Fungsi |
|---|---|---|
| POST | `/` | Buat post (gambar + caption), beri poin. |
| GET | `/` | Feed post (paginasi), termasuk jumlah like/komentar & status `is_liked`. |
| GET | `/{post_id}` | Detail post + semua komentar. |
| POST | `/{post_id}/like` | Toggle like. |
| POST | `/{post_id}/comment` | Tambah komentar. |

### 4.11 Konten Edukasi & Reward
| Domain | Endpoint | Fungsi |
|---|---|---|
| Video — `/api/video` | `GET /`, `POST /claim-point` | List video edukasi; klaim poin nonton (1x per video). |
| Resep — `/api/recipe` | `GET /`, `POST /claim-point` | List resep sehat; klaim poin baca (1x per resep). |
| Game — `/api/games` | `GET /`, `GET /{id}/play`, `POST /{id}/claim` | List game; mainkan (jika sudah diklaim); klaim game dengan menukar credit points. |
| Merchandise — `/api/merchandise` | `GET /`, `POST /claim` | List merchandise; ajukan klaim (menunggu approval admin) dengan menukar credit points. |
| Leaderboard — `/api/point` | `GET /leaderboard` | Ranking semua pengguna berdasarkan achievement points. |

### 4.12 Dashboard Admin — `/dashboard`
Autentikasi cookie session (`admin_access`), bukan bearer token. Semua form `POST` dilindungi CSRF token.

| Area | Endpoint utama | Fungsi |
|---|---|---|
| Login | `GET/POST /login`, `POST /logout` | Login admin & kelola sesi. |
| Pengguna | `GET /users`, `GET /users/{id}`, `POST /users/{id}/delete`, `GET/POST /reset/password[/confirm]` | Kelola & moderasi akun pengguna, reset password atas nama user. |
| Resep | `GET /recipes`, `GET/POST /recipes/upload` | Kelola konten resep. |
| Video | `GET /videos`, `GET/POST /videos/create`, `POST /videos/delete/{id}`, `POST /videos/toggle/{id}` | Kelola konten video edukasi + status aktif/nonaktif. |
| Game | `GET /games`, `GET/POST /games/create`, `GET /games/{id}/view` | Kelola katalog game. |
| Makanan | `GET /foods`, `GET/POST /foods/create`, `POST /foods/update/{id}`, `POST /foods/delete/{id}` | Kelola database referensi makanan/kalori. |
| Merchandise | `GET/POST /merchandise/upload`, `GET /merchandise`, `POST /merchandise/update/{id}`, `GET /merchandise/claims`, `POST /merchandise/claims/{id}/approve|reject` | Kelola katalog merchandise & approval klaim redeem. |
| Profesional | `GET /professionals`, `GET/POST /professionals/create`, `GET /professionals/{id}/edit`, `POST /professionals/{id}/update|delete` | Kelola data dokter/psikolog termasuk jadwal ketersediaan per hari. |
| Appointment | `GET /appointments`, `POST /appointments/update/{id}/{status}`, `POST /appointments/delete/{id}` | Alternatif in-dashboard untuk konfirmasi/tolak/hapus appointment (selain via email). |
| Transaksi Poin | `GET /transactions`, `GET /transactions/export` | Lihat & ekspor (Excel) buku besar transaksi poin. |
| Leaderboard | `GET /leaderboard` | Lihat ranking poin seluruh pengguna. |
| Ekspor Data Kesehatan | `GET /export/health-data` | Ekspor massal data gizi/kesehatan pengguna ke Excel. |
| Email Blast | `GET/POST /blast`, `GET /blast/{id}/detail`, `GET /api/blast/{id}/status`, `POST /blast/{id}/retry` | Kirim email massal ke segmen pengguna, pantau progres pengiriman, retry yang gagal. |

### 4.13 Halaman Publik Lain
- `GET /` → redirect ke `/dashboard/login`.
- `GET /privacy-policy`, `GET /term-of-service` → halaman kebijakan (statis, Jinja2).

---

## 5. Modul Data Inti (Model)

| Model | Makna bisnis |
|---|---|
| `user.py` | Akun/profil pengguna — entitas pusat tempat data domain lain menggantung, punya flag role (user/admin). |
| `user_nutrition.py` | Snapshot pengukuran tubuh (tinggi/berat/BMI/status/berat ideal) pada satu waktu. |
| `bmi_reference.py` | Tabel referensi standar deviasi BMI-for-age (WHO) per gender/usia, dasar perhitungan z-score gizi. |
| `food.py` | Database referensi makanan/kalori, kuesioner DQQ, dan entri food diary harian. |
| `exercise_habit.py` | Kuesioner PAQ-A dan jawaban harian pengguna. |
| `sleep.py` | Catatan sesi tidur (waktu tidur/bangun, durasi, target). |
| `reminder.py` | Pengingat berulang milik pengguna (jam, hari aktif, pesan). |
| `point.py` | Sistem gamifikasi — kategori poin, dompet ganda (achievement/credit) per pengguna, buku besar transaksi. |
| `games.py` | Katalog game yang bisa diklaim dengan poin + status klaim per pengguna. |
| `merchandise.py` | Katalog merchandise fisik yang bisa ditukar poin + status klaim (pending/approved/rejected). |
| `recipe.py` | Konten resep sehat + catatan klaim poin "baca resep". |
| `video.py` | Katalog video edukasi + catatan klaim poin "tonton video". |
| `forum.py` | Post forum sosial (gambar+caption) beserta like dan komentar. |
| `chat.py` | Room chat 1:1, partisipan, dan riwayat pesan. |
| `professionals.py` | Data dokter/psikolog (termasuk jadwal ketersediaan) dan appointment yang dibuat pengguna terhadap mereka. |
| `blast_log.py` | Log pengiriman email blast massal (subjek/isi/penerima/hasil kirim) oleh admin. |

---

## 6. Logika Bisnis Kunci

**Kalkulator Gizi** (`app/src/utils/nutrition_calculator.py`)
Menghitung BMI dari berat/tinggi, mencocokkan ke tabel `BMIReference` (standar deviasi WHO) berdasarkan usia tepat (tahun+bulan) dengan interpolasi antar band usia, lalu mengklasifikasikan status gizi (Severely Underweight/Underweight/Normal/Overweight/Obese). Juga menghitung berat badan ideal (rumus Broca — potongan 10% untuk laki-laki, 15% untuk perempuan) dan Estimated Energy Requirement (EER) memakai persamaan IOM/DRI dengan koefisien aktivitas fisik berbeda per gender. **Dibatasi hingga usia 19 tahun 0 bulan** — sesuai target populasi remaja aplikasi ini, di luar itu akan raise error.

**Sistem Poin** (`app/src/utils/point_service.py`)
`reward_user_points` mengambil nilai poin dari `PointCategory` lalu mengkredit dua dompet sekaligus (achievement + credit) dengan satu baris transaksi per dompet. `redeem_merchandise_points`/`claim_games` adalah alur sebaliknya: cek saldo credit cukup, debit, catat transaksi. Pengecekan "sudah klaim/submit hari ini" jadi tanggung jawab masing-masing endpoint pemanggil, bukan service ini.

---

## 7. Menjalankan Secara Lokal

```bash
poetry install
# buat file .env berisi DATABASE_URL, REDIS_*, SMTP_*, SECRET_KEY, dst — lihat app/src/core/config.py
alembic upgrade head
uvicorn main:app --reload
```

Variabel environment wajib (lihat `app/src/core/config.py`): `SECRET_KEY`, `DATABASE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SENDER`. Redis (`REDIS_HOST`/`REDIS_PORT`) dipakai untuk state registrasi/reset-password sementara.

Dokumentasi interaktif API tersedia otomatis di `/docs` (Swagger UI) selama server berjalan.

## 8. Deployment

Push ke branch `main` men-trigger GitHub Actions (`.github/workflows/deploy.yml`) yang SSH ke VPS dan menjalankan `deploy.sh`.
