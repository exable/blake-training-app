# Blake's Training App

A full-stack personal training/nutrition/check-in app with an embedded AI coach (Ero) powered by the Anthropic API.

- **Frontend:** React + Vite + Tailwind CSS (dark mode, responsive)
- **Backend:** Flask + SQLAlchemy + JWT auth
- **Database:** PostgreSQL (SQLite fallback in dev)
- **AI:** Anthropic `claude-sonnet-4-20250514`
- **Photo storage:** Cloudinary
- **Hosting:** Railway or Render

## Project layout

```
blake-training-app/
├── backend/        Flask API + seed script
├── frontend/       React app
├── render.yaml     Render Blueprint
├── railway.json    Railway config
└── README.md
```

## Local setup

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env       # then edit .env
python seed.py             # creates user, seeds meals & lifts
flask --app app run --port 5000
```

Required `.env` values:

| var | what it's for |
| --- | --- |
| `SECRET_KEY` | Flask session + JWT signing |
| `DATABASE_URL` | e.g. `postgresql://user:pass@localhost:5432/blake_training` — omit for SQLite |
| `ANTHROPIC_API_KEY` | Ero AI chat & weekly responses |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Progress photo uploads |
| `BLAKE_PASSWORD` | Sets Blake's login password on first run |
| `FRONTEND_ORIGIN` | CORS origin in prod e.g. `https://app.example.com` |

On first run the app creates user `blake` with `BLAKE_PASSWORD`, seeds the 6 pre-set meals, and populates the most recent logged weights for each exercise.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173 — proxies /api → :5000
```

For a prod build pointed at a remote API, set `VITE_API_BASE` in `frontend/.env`:

```
VITE_API_BASE=https://your-api.up.railway.app
```

### 3. Log in

Open http://localhost:5173 → username `blake`, password from `BLAKE_PASSWORD`.

## Re-running the seed

`seed.py` and the auto-seed at app start are both idempotent — they only insert data when the corresponding tables are empty for Blake's user.

To wipe and reseed (dev only):

```bash
rm backend/blake.db        # or drop and recreate the Postgres DB
python seed.py
```

## Deploying to Railway

1. Create a new Railway project from this repo.
2. Add a **PostgreSQL plugin** — Railway will inject `DATABASE_URL`.
3. Set the remaining env vars in the service: `SECRET_KEY`, `ANTHROPIC_API_KEY`, the 3 Cloudinary vars, `BLAKE_PASSWORD`, `FRONTEND_ORIGIN`.
4. Railway reads `railway.json`; it builds from `backend/` and starts via `gunicorn app:app`.
5. (Optional) Deploy the frontend as a second Railway service or to Vercel/Netlify. Build command: `npm install && npm run build`. Output: `dist/`. Set `VITE_API_BASE` to the API URL.

## Deploying to Render

1. Click **New + Blueprint** in Render, point at this repo. Render reads `render.yaml`.
2. It will provision: API service, static web service, and a Postgres DB.
3. Fill in the secrets: `ANTHROPIC_API_KEY`, `CLOUDINARY_*`, `BLAKE_PASSWORD`, `FRONTEND_ORIGIN` (the web service's URL), `VITE_API_BASE` (the API service's URL).
4. Render injects `DATABASE_URL` from the managed Postgres.

## Features

- Dashboard with day-at-a-glance (weight, today's session, meals eaten, water, check-in status).
- Workout: auto-suggests the ULPPL session for the day; live logging with per-set rest timer that auto-starts; previous weight/reps shown above each input; full history filterable by session type.
- Nutrition: 6 pre-set meals, eat toggles, live macro totals vs targets, water tracker with quick-add buttons and custom input, full edit/add of meals.
- Daily check-in: weight, 3 proud-ofs, sleep slider, nutrition adherence, trained today, notes — locked after submit. Ero acknowledges immediately in chat.
- Weekly check-in (unlocks every Monday): full questionnaire, 1–10 sliders, front/side/back photo uploads to Cloudinary. Ero's tailored response is delivered to chat after a randomised 1–8 hour delay (triggered when you next open the app — call `/api/checkins/weekly/process-pending`).
- Progress: bodyweight chart with goal/start reference lines + 7-day rolling average, per-exercise progress chart with PB, photo gallery with side-by-side comparison.
- Chat with Ero: persistent thread, optimistic UI, typing indicator, real Anthropic API calls. Ero's system prompt is loaded from `backend/program.py`.
- Settings: change password, edit calorie/macro/water/goal targets, export everything as JSON.
- Form drafts persist in `localStorage` — page refresh during a workout or weekly check-in does not lose your inputs.

## Notes

- Ero's weekly-check-in response is scheduled at a random 1–8 hour offset (`WeeklyCheckin.ero_response_scheduled_at`). It is generated server-side when `/api/checkins/weekly/process-pending` runs (the frontend invokes this on every app load). For production-grade scheduled delivery, wire this endpoint to a cron job.
- Tokens are issued with a 30-day expiry — change `JWT_ACCESS_TOKEN_EXPIRES` in `config.py` if you want shorter sessions.
- Mobile layout uses a bottom tab bar (with safe-area inset); desktop uses a left sidebar at the `md` breakpoint.
