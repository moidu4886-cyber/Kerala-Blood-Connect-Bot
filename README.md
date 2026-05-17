# 🩸 Kerala Blood Connect Bot

A production-ready Telegram bot that connects blood donors with patients across all 14 Kerala districts. Built with Python 3, aiogram 3, and MongoDB Atlas.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🧑‍💼 Donor Registration | Step-by-step FSM flow: name, phone, blood group, district, area, last donation |
| 🔍 Smart Search | Filter by blood group + district, paginated results |
| 🚨 Emergency Alerts | Auto-broadcasts to matching donors in real time |
| 👤 Profile Management | View, edit any field, toggle availability |
| 📢 Admin Broadcast | Send messages to all users |
| 📊 Admin Stats | Per-district, per-blood-group donor breakdown |
| 📋 CSV Export | Download full donor list as CSV |
| 🗑️ Auto-cleanup | Old emergency requests auto-deleted every hour |
| 🔔 Donation Reminders | Daily check notifies donors eligible after 90 days |
| 🛡️ Security | Rate limiting, phone/name/date validation, admin guard |

---

## 📁 Project Structure

```
kerala_blood_bot/
├── bot.py              ← Entry point; bot + dispatcher setup
├── config.py           ← Environment variables + constants
├── database.py         ← All MongoDB operations (Motor async)
├── states.py           ← FSM state groups
├── keyboards.py        ← All InlineKeyboardMarkup builders
│
├── handlers/
│   ├── start.py        ← /start, main menu, help, share
│   ├── register.py     ← 6-step donor registration
│   ├── search.py       ← Find donor with pagination
│   ├── emergency.py    ← Emergency request + broadcast
│   ├── profile.py      ← View profile, edit fields, toggle availability
│   └── admin.py        ← Admin dashboard, stats, broadcast, export
│
├── utils/
│   ├── validators.py   ← Input validation (name, phone, date, etc.)
│   ├── helpers.py      ← Message formatters + rate limiter
│   └── broadcast.py    ← Async broadcast utility
│
├── requirements.txt
├── Procfile            ← For Koyeb / Render / Railway
├── .env.example
└── README.md
```

---

## 🚀 Deployment

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd kerala_blood_bot
pip install -r requirements.txt
```

### 2. Create `.env`

```bash
cp .env.example .env
```

Fill in:
- `BOT_TOKEN` — From [@BotFather](https://t.me/BotFather)
- `MONGO_URI` — From [MongoDB Atlas](https://www.mongodb.com/atlas)
- `ADMIN_ID` — Your Telegram user ID (from [@userinfobot](https://t.me/userinfobot))

### 3. Run Locally

```bash
python bot.py
```

---

## ☁️ Deploy to Render

1. Push this project to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Set **Start Command**: `python bot.py`
4. Add environment variables in the Render dashboard
5. Deploy!

## ☁️ Deploy to Koyeb

1. Push to GitHub
2. Create a new Koyeb app → Connect GitHub repo
3. Set **Run Command**: `python bot.py`
4. Add env vars: `BOT_TOKEN`, `MONGO_URI`, `ADMIN_ID`
5. Deploy!

## ☁️ Deploy to Railway

1. `railway login && railway init`
2. `railway up`
3. Set env vars in Railway dashboard

---

## 🗄️ MongoDB Atlas Setup

1. Go to [MongoDB Atlas](https://cloud.mongodb.com) → Create free cluster
2. Create a database user with read/write access
3. Whitelist IP: `0.0.0.0/0` (allow all — required for cloud deployment)
4. Get connection string → replace `<password>` → paste in `.env`

The bot auto-creates these collections and indexes on first run:
- `users` — Registered donors
- `emergency_requests` — Active emergency requests

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Open main menu |
| `/register` | Become a blood donor |
| `/find` | Search for donors |
| `/emergency` | Post emergency request |
| `/profile` | View your profile |
| `/availability` | Toggle donor status |
| `/help` | Help & instructions |
| `/admin` | Admin panel (admin only) |

---

## 🛡️ Security

- **Rate limiting**: 2-second cooldown between actions per user
- **Input validation**: All text inputs validated (phone, date format, length)
- **Admin guard**: Admin functions check Telegram ID against `ADMIN_ID` env var
- **Spam protection**: Forbidden errors caught gracefully during broadcasts

---

## 🩸 Blood Groups Supported

`A+` `A-` `B+` `B-` `AB+` `AB-` `O+` `O-`

## 📍 Districts Covered

All 14 Kerala districts:
Thiruvananthapuram, Kollam, Pathanamthitta, Alappuzha, Kottayam, Idukki,
Ernakulam, Thrissur, Palakkad, Malappuram, Kozhikode, Wayanad, Kannur, Kasaragod

---

## 📜 License

MIT License — Free to use and modify.

---

*Made with ❤️ for Kerala. Every drop counts. 🙏*
