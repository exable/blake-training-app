import os
import json
import random
from datetime import datetime, date, timedelta, time
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import inspect, text
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func
import cloudinary
import cloudinary.uploader

from config import Config
from extensions import db, jwt, cors, migrate
from models import (
    User, WeightLog, WorkoutSession, WorkoutSet, Meal, MealLog, WaterLog,
    DailyCheckin, WeeklyCheckin, ProgressPhoto, ChatMessage, ExercisePrevious,
)
from program import PROGRAM, DAY_TO_SESSION, SEED_MEALS, RECENT_LIFTS
from ero import (
    chat_with_ero, chat_with_ero_multimodal,
    generate_daily_acknowledgement, generate_weekly_response, proactive_check,
)


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    db.init_app(app)
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    scheme = uri.split("://", 1)[0] if "://" in uri else "?"
    print(f"[db] scheme={scheme}", flush=True)
    jwt.init_app(app)
    migrate.init_app(app, db)

    origin = Config.FRONTEND_ORIGIN
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origin if origin != "*" else "*"}},
        supports_credentials=True,
    )

    if Config.CLOUDINARY_CLOUD_NAME:
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET,
            secure=True,
        )

    register_routes(app)

    with app.app_context():
        db.create_all()
        ensure_schema()
        ensure_seed()
        cleanup_stale_sessions()

    return app


def ensure_schema():
    """Idempotent column migrations so old DBs catch up to the model."""
    try:
        insp = inspect(db.engine)
        if "workout_sessions" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("workout_sessions")}
            if "difficulty" not in cols:
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE workout_sessions ADD COLUMN difficulty INTEGER"))
                print("[migration] added workout_sessions.difficulty", flush=True)
    except Exception as e:
        print(f"[migration] failed: {e}", flush=True)


def cleanup_stale_sessions():
    """One-time cleanup: delete any incomplete sessions left over from buggy days.
    Going forward there should only ever be at most one in-progress session per user
    (enforced by the start_session endpoint)."""
    try:
        stale = WorkoutSession.query.filter(WorkoutSession.completed_at == None).all()
        if stale:
            for s in stale:
                db.session.delete(s)
            db.session.commit()
            print(f"[cleanup] removed {len(stale)} incomplete sessions", flush=True)
    except Exception as e:
        print(f"[cleanup] failed: {e}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_user() -> User:
    uid = int(get_jwt_identity())
    return db.session.get(User, uid)


def todays_session_type() -> str:
    return DAY_TO_SESSION[date.today().weekday()]


def iso_utc(dt):
    """Serialize a naive UTC datetime with explicit 'Z' suffix so JS parses it as UTC."""
    if dt is None:
        return None
    # Strip any tz and force Z (we store UTC naively via datetime.utcnow())
    return dt.replace(tzinfo=None).isoformat() + "Z"


def serialize_session(s: WorkoutSession) -> dict:
    sets = WorkoutSet.query.filter_by(session_id=s.id).order_by(WorkoutSet.id.asc()).all()
    return {
        "id": s.id,
        "session_type": s.session_type,
        "started_at": iso_utc(s.started_at),
        "completed_at": iso_utc(s.completed_at),
        "notes": s.notes,
        "difficulty": getattr(s, "difficulty", None),
        "sets": [
            {
                "id": st.id,
                "exercise_name": st.exercise_name,
                "set_number": st.set_number,
                "weight_kg": st.weight_kg,
                "reps": st.reps,
                "rpe": st.rpe,
                "logged_at": iso_utc(st.logged_at),
            } for st in sets
        ],
    }


def get_previous_for(user_id: int, session_type: str) -> dict:
    rows = ExercisePrevious.query.filter_by(user_id=user_id, session_type=session_type).all()
    return {r.exercise_name: json.loads(r.sets_json) for r in rows}


def compute_achievements(session: WorkoutSession) -> list[dict]:
    """
    Compare current session's sets vs the cached previous sets for each exercise.
    Detects: heavier top set, extra set added, more reps at same weight, heavier same-set, etc.
    Must be called BEFORE update_previous_from_session() so the cache still holds the prior values.
    """
    current_sets = (WorkoutSet.query.filter_by(session_id=session.id)
                    .order_by(WorkoutSet.id.asc()).all())
    by_ex: dict[str, list[WorkoutSet]] = {}
    for s in current_sets:
        by_ex.setdefault(s.exercise_name, []).append(s)

    out = []
    for ex_name, cur_sets in by_ex.items():
        # Skip cardio placeholders (weight=0, reps<=1)
        if all(c.weight_kg == 0 and c.reps <= 1 for c in cur_sets):
            continue

        prev_row = ExercisePrevious.query.filter_by(
            user_id=session.user_id,
            session_type=session.session_type,
            exercise_name=ex_name,
        ).first()
        if not prev_row:
            continue
        prev_sets = json.loads(prev_row.sets_json)
        if not prev_sets:
            continue

        wins: list[str] = []

        cur_max = max(c.weight_kg for c in cur_sets)
        prev_max = max(p["weight_kg"] for p in prev_sets)
        if cur_max > prev_max:
            wins.append(f"new top weight: {cur_max}kg (prev {prev_max}kg)")

        if len(cur_sets) > len(prev_sets):
            wins.append(f"added a set ({len(prev_sets)} → {len(cur_sets)})")

        # Per-set comparison
        for i, cs in enumerate(cur_sets):
            if i >= len(prev_sets):
                continue
            ps = prev_sets[i]
            if cs.weight_kg > ps["weight_kg"]:
                wins.append(
                    f"set {i + 1}: {cs.weight_kg}kg × {cs.reps} (prev {ps['weight_kg']}kg × {ps['reps']})"
                )
            elif cs.weight_kg == ps["weight_kg"] and cs.reps > ps["reps"]:
                wins.append(
                    f"set {i + 1}: {cs.reps} reps @ {cs.weight_kg}kg (prev {ps['reps']})"
                )

        # Volume: total reps × weight
        cur_vol = sum(c.weight_kg * c.reps for c in cur_sets)
        prev_vol = sum(p["weight_kg"] * p["reps"] for p in prev_sets)
        if cur_vol > prev_vol * 1.02 and not wins:  # ≥2% volume bump even if no per-set win
            wins.append(f"total volume up {int((cur_vol / prev_vol - 1) * 100)}%")

        if wins:
            out.append({"exercise": ex_name, "wins": wins})

    return out


def update_previous_from_session(session: WorkoutSession):
    """After a session is completed, update ExercisePrevious cache."""
    sets = WorkoutSet.query.filter_by(session_id=session.id).order_by(WorkoutSet.id.asc()).all()
    by_ex: dict[str, list] = {}
    for s in sets:
        by_ex.setdefault(s.exercise_name, []).append({"weight_kg": s.weight_kg, "reps": s.reps})
    for ex, sets_list in by_ex.items():
        row = ExercisePrevious.query.filter_by(
            user_id=session.user_id, session_type=session.session_type, exercise_name=ex
        ).first()
        if not row:
            row = ExercisePrevious(
                user_id=session.user_id, session_type=session.session_type, exercise_name=ex,
                sets_json=json.dumps(sets_list),
            )
            db.session.add(row)
        else:
            row.sets_json = json.dumps(sets_list)
            row.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def ensure_seed():
    user = User.query.filter_by(username=Config.BLAKE_USERNAME).first()
    if not user:
        user = User(username=Config.BLAKE_USERNAME)
        password = Config.BLAKE_PASSWORD or "changeme"
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"[seed] Created user '{Config.BLAKE_USERNAME}'.")

    # Seed meals if none
    if Meal.query.filter_by(user_id=user.id).count() == 0:
        for m in SEED_MEALS:
            db.session.add(Meal(user_id=user.id, is_active=True, **m))
        db.session.commit()
        print(f"[seed] Seeded {len(SEED_MEALS)} meals.")

    # Seed/back-fill exercise previous — idempotent. Only inserts entries that don't already exist
    # so user-logged sessions are NEVER overwritten.
    added = 0
    for stype, exs in RECENT_LIFTS.items():
        for ex_name, sets_list in exs.items():
            existing = ExercisePrevious.query.filter_by(
                user_id=user.id, session_type=stype, exercise_name=ex_name,
            ).first()
            if existing:
                continue
            db.session.add(ExercisePrevious(
                user_id=user.id, session_type=stype, exercise_name=ex_name,
                sets_json=json.dumps(sets_list),
            ))
            added += 1
    if added:
        db.session.commit()
        print(f"[seed] Added/backfilled {added} ExercisePrevious rows.")

    # Seed starting bodyweight if none
    if WeightLog.query.filter_by(user_id=user.id).count() == 0:
        db.session.add(WeightLog(user_id=user.id, weight_kg=65.3))
        db.session.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def register_routes(app: Flask):

    @app.get("/api/health")
    def health():
        return {"ok": True, "time": datetime.utcnow().isoformat()}

    # -------- AUTH --------
    @app.post("/api/auth/login")
    def login():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip().lower()
        password = data.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return {"error": "Invalid credentials"}, 401
        token = create_access_token(identity=str(user.id))
        return {"token": token, "user": {"id": user.id, "username": user.username}}

    @app.post("/api/auth/change-password")
    @jwt_required()
    def change_password():
        data = request.get_json(force=True)
        old = data.get("old_password") or ""
        new = data.get("new_password") or ""
        u = current_user()
        if not u.check_password(old):
            return {"error": "Current password incorrect"}, 400
        if len(new) < 6:
            return {"error": "Password must be at least 6 characters"}, 400
        u.set_password(new)
        db.session.commit()
        return {"ok": True}

    @app.get("/api/me")
    @jwt_required()
    def me():
        u = current_user()
        return {
            "id": u.id, "username": u.username,
            "daily_calorie_target": u.daily_calorie_target,
            "daily_protein_target": u.daily_protein_target,
            "daily_carb_target": u.daily_carb_target,
            "daily_fat_target": u.daily_fat_target,
            "daily_water_target_ml": u.daily_water_target_ml,
            "goal_weight_kg": u.goal_weight_kg,
            "starting_weight_kg": u.starting_weight_kg,
        }

    @app.put("/api/me/targets")
    @jwt_required()
    def update_targets():
        u = current_user()
        data = request.get_json(force=True)
        for f in ("daily_calorie_target", "daily_protein_target", "daily_carb_target",
                  "daily_fat_target", "daily_water_target_ml"):
            if f in data:
                setattr(u, f, int(data[f]))
        if "goal_weight_kg" in data:
            u.goal_weight_kg = float(data["goal_weight_kg"])
        db.session.commit()
        return {"ok": True}

    # -------- DASHBOARD --------
    @app.get("/api/dashboard")
    @jwt_required()
    def dashboard():
        u = current_user()
        today = date.today()

        latest_weight = (WeightLog.query.filter_by(user_id=u.id)
                         .order_by(WeightLog.logged_at.desc()).first())

        session_type = todays_session_type()
        todays_session = (WorkoutSession.query
                          .filter(WorkoutSession.user_id == u.id,
                                  func.date(WorkoutSession.started_at) == today)
                          .order_by(WorkoutSession.started_at.desc()).first())

        meals = Meal.query.filter_by(user_id=u.id, is_active=True).all()
        meal_logs = MealLog.query.filter_by(user_id=u.id, date=today).all()
        eaten_map = {ml.meal_id: ml.eaten for ml in meal_logs}
        eaten_count = sum(1 for m in meals if eaten_map.get(m.id))
        total_meals = len(meals)

        water_total = sum(w.amount_ml for w in WaterLog.query.filter_by(user_id=u.id, date=today).all())

        daily_done = DailyCheckin.query.filter_by(user_id=u.id, date=today).first() is not None

        return {
            "date": today.isoformat(),
            "latest_weight_kg": latest_weight.weight_kg if latest_weight else None,
            "session_type_today": session_type,
            "session_started": bool(todays_session),
            "session_completed": bool(todays_session and todays_session.completed_at),
            "meals_eaten": eaten_count,
            "meals_total": total_meals,
            "water_ml": water_total,
            "water_target_ml": u.daily_water_target_ml,
            "daily_checkin_done": daily_done,
        }

    # -------- WEIGHT --------
    @app.get("/api/weights")
    @jwt_required()
    def list_weights():
        u = current_user()
        rows = WeightLog.query.filter_by(user_id=u.id).order_by(WeightLog.logged_at.asc()).all()
        return [{"id": r.id, "weight_kg": r.weight_kg, "logged_at": r.logged_at.isoformat()} for r in rows]

    @app.post("/api/weights")
    @jwt_required()
    def add_weight():
        u = current_user()
        data = request.get_json(force=True)
        w = WeightLog(user_id=u.id, weight_kg=float(data["weight_kg"]))
        db.session.add(w)
        db.session.commit()
        return {"id": w.id, "weight_kg": w.weight_kg, "logged_at": w.logged_at.isoformat()}

    # -------- PROGRAM --------
    @app.get("/api/program")
    @jwt_required()
    def get_program():
        u = current_user()
        out = {}
        for stype, exs in PROGRAM.items():
            prev = get_previous_for(u.id, stype)
            out[stype] = {
                "exercises": exs,
                "previous": prev,
            }
        out["_today"] = todays_session_type()
        return out

    # -------- WORKOUT SESSIONS --------
    @app.get("/api/sessions")
    @jwt_required()
    def list_sessions():
        u = current_user()
        stype = request.args.get("session_type")
        # History only shows COMPLETED sessions — in-progress sessions are never historical
        q = WorkoutSession.query.filter(
            WorkoutSession.user_id == u.id,
            WorkoutSession.completed_at != None,
        )
        if stype:
            q = q.filter_by(session_type=stype)
        sessions = q.order_by(WorkoutSession.completed_at.desc()).limit(100).all()
        return [serialize_session(s) for s in sessions]

    @app.get("/api/sessions/in-progress")
    @jwt_required()
    def in_progress_session():
        u = current_user()
        s = (WorkoutSession.query
             .filter(WorkoutSession.user_id == u.id, WorkoutSession.completed_at == None)
             .order_by(WorkoutSession.started_at.desc())
             .first())
        if not s:
            return {"in_progress": False}
        return {"in_progress": True, "session": serialize_session(s)}

    @app.get("/api/sessions/<int:sid>")
    @jwt_required()
    def get_session(sid):
        u = current_user()
        s = WorkoutSession.query.filter_by(id=sid, user_id=u.id).first_or_404()
        return serialize_session(s)

    @app.post("/api/sessions")
    @jwt_required()
    def start_session():
        u = current_user()
        data = request.get_json(force=True)
        stype = data.get("session_type") or todays_session_type()
        force_new = bool(data.get("force_new"))
        today = date.today()

        # 1-completed-per-day rule
        completed_today = (WorkoutSession.query
                           .filter(WorkoutSession.user_id == u.id,
                                   WorkoutSession.completed_at != None,
                                   func.date(WorkoutSession.completed_at) == today)
                           .first())
        if completed_today:
            return {"error": "You've already completed a workout today."}, 400

        # If there's already an in-progress session, return it (don't silently nuke its data)
        existing = (WorkoutSession.query
                    .filter(WorkoutSession.user_id == u.id,
                            WorkoutSession.completed_at == None)
                    .order_by(WorkoutSession.started_at.desc())
                    .first())
        if existing and not force_new:
            # Same type → resume. Different type → tell the client to confirm.
            if existing.session_type == stype:
                out = serialize_session(existing)
                out["resumed"] = True
                return out
            return {
                "error": (
                    f"You already have a {existing.session_type} session in progress "
                    "started earlier. Cancel it first, or pass force_new=true to discard it."
                ),
                "active_session_type": existing.session_type,
                "active_session_id": existing.id,
            }, 409

        if existing and force_new:
            db.session.delete(existing)
            db.session.commit()

        s = WorkoutSession(user_id=u.id, session_type=stype, started_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        out = serialize_session(s)
        out["resumed"] = False
        return out

    @app.post("/api/sessions/<int:sid>/cancel")
    @jwt_required()
    def cancel_session(sid):
        u = current_user()
        s = WorkoutSession.query.filter_by(id=sid, user_id=u.id).first_or_404()
        if s.completed_at:
            return {"error": "Session already completed — can't cancel."}, 400
        db.session.delete(s)
        db.session.commit()
        return {"ok": True}

    @app.post("/api/sessions/<int:sid>/sets")
    @jwt_required()
    def log_set(sid):
        u = current_user()
        s = WorkoutSession.query.filter_by(id=sid, user_id=u.id).first_or_404()
        data = request.get_json(force=True)
        st = WorkoutSet(
            session_id=s.id,
            exercise_name=data["exercise_name"],
            set_number=int(data["set_number"]),
            weight_kg=float(data["weight_kg"]),
            reps=int(data["reps"]),
            rpe=float(data["rpe"]) if data.get("rpe") not in (None, "") else None,
        )
        db.session.add(st)
        db.session.commit()
        return {"id": st.id}

    @app.post("/api/sessions/<int:sid>/complete")
    @jwt_required()
    def complete_session(sid):
        u = current_user()
        s = WorkoutSession.query.filter_by(id=sid, user_id=u.id).first_or_404()
        if s.completed_at:
            return {"error": "Session already completed."}, 400

        today = date.today()
        already_completed_today = (WorkoutSession.query
                                   .filter(WorkoutSession.user_id == u.id,
                                           WorkoutSession.id != s.id,
                                           WorkoutSession.completed_at != None,
                                           func.date(WorkoutSession.completed_at) == today)
                                   .first())
        if already_completed_today:
            return {"error": "You've already completed a workout today."}, 400

        data = request.get_json(silent=True) or {}
        s.completed_at = datetime.utcnow()
        s.notes = data.get("notes", "") or s.notes
        if data.get("difficulty") not in (None, ""):
            s.difficulty = int(data.get("difficulty"))

        # Achievements BEFORE updating cache so we still see the prior values
        achievements = compute_achievements(s)
        update_previous_from_session(s)
        db.session.commit()

        result = serialize_session(s)
        result["achievements"] = achievements
        result["difficulty"] = s.difficulty
        return result

    @app.delete("/api/sessions/<int:sid>")
    @jwt_required()
    def delete_session(sid):
        u = current_user()
        s = WorkoutSession.query.filter_by(id=sid, user_id=u.id).first_or_404()
        db.session.delete(s)
        db.session.commit()
        return {"ok": True}

    # -------- EXERCISE PROGRESS --------
    @app.get("/api/exercise-progress")
    @jwt_required()
    def exercise_progress():
        u = current_user()
        name = request.args.get("exercise_name")
        if not name:
            # return list of distinct exercise names from COMPLETED sessions only
            rows = (db.session.query(WorkoutSet.exercise_name)
                    .join(WorkoutSession, WorkoutSession.id == WorkoutSet.session_id)
                    .filter(WorkoutSession.user_id == u.id,
                            WorkoutSession.completed_at != None)
                    .distinct().all())
            return {"exercises": sorted([r[0] for r in rows])}
        rows = (db.session.query(WorkoutSet, WorkoutSession)
                .join(WorkoutSession, WorkoutSession.id == WorkoutSet.session_id)
                .filter(WorkoutSession.user_id == u.id,
                        WorkoutSession.completed_at != None,
                        WorkoutSet.exercise_name == name)
                .order_by(WorkoutSet.logged_at.asc()).all())
        points = []
        pb = 0.0
        for st, sess in rows:
            points.append({
                "logged_at": st.logged_at.isoformat(),
                "weight_kg": st.weight_kg,
                "reps": st.reps,
            })
            if st.weight_kg > pb:
                pb = st.weight_kg
        return {"exercise_name": name, "points": points, "personal_best_kg": pb}

    # -------- MEALS --------
    @app.get("/api/meals")
    @jwt_required()
    def list_meals():
        u = current_user()
        today = date.today()
        meals = Meal.query.filter_by(user_id=u.id, is_active=True).order_by(Meal.sort_order.asc()).all()
        logs = {ml.meal_id: ml for ml in MealLog.query.filter_by(user_id=u.id, date=today).all()}
        out = []
        for m in meals:
            ml = logs.get(m.id)
            out.append({
                "id": m.id, "name": m.name, "scheduled_time": m.scheduled_time,
                "calories": m.calories, "protein": m.protein, "carbs": m.carbs, "fat": m.fat,
                "sort_order": m.sort_order,
                "eaten": bool(ml and ml.eaten),
            })
        return out

    @app.post("/api/meals")
    @jwt_required()
    def create_meal():
        u = current_user()
        data = request.get_json(force=True)
        max_order = db.session.query(func.max(Meal.sort_order)).filter_by(user_id=u.id).scalar() or 0
        m = Meal(
            user_id=u.id, name=data["name"],
            scheduled_time=data.get("scheduled_time", ""),
            calories=int(data.get("calories", 0)),
            protein=int(data.get("protein", 0)),
            carbs=int(data.get("carbs", 0)),
            fat=int(data.get("fat", 0)),
            sort_order=int(data.get("sort_order", max_order + 1)),
            is_active=True,
        )
        db.session.add(m)
        db.session.commit()
        return {"id": m.id}

    @app.put("/api/meals/<int:mid>")
    @jwt_required()
    def update_meal(mid):
        u = current_user()
        m = Meal.query.filter_by(id=mid, user_id=u.id).first_or_404()
        data = request.get_json(force=True)
        for f in ("name", "scheduled_time"):
            if f in data:
                setattr(m, f, data[f])
        for f in ("calories", "protein", "carbs", "fat", "sort_order"):
            if f in data:
                setattr(m, f, int(data[f]))
        if "is_active" in data:
            m.is_active = bool(data["is_active"])
        db.session.commit()
        return {"ok": True}

    @app.delete("/api/meals/<int:mid>")
    @jwt_required()
    def delete_meal(mid):
        u = current_user()
        m = Meal.query.filter_by(id=mid, user_id=u.id).first_or_404()
        m.is_active = False
        db.session.commit()
        return {"ok": True}

    @app.post("/api/meals/<int:mid>/toggle")
    @jwt_required()
    def toggle_meal(mid):
        u = current_user()
        today = date.today()
        m = Meal.query.filter_by(id=mid, user_id=u.id).first_or_404()
        log = MealLog.query.filter_by(user_id=u.id, meal_id=m.id, date=today).first()
        if not log:
            log = MealLog(user_id=u.id, meal_id=m.id, date=today, eaten=True)
            db.session.add(log)
        else:
            log.eaten = not log.eaten
            log.logged_at = datetime.utcnow()
        db.session.commit()
        return {"eaten": log.eaten}

    # -------- WATER --------
    @app.get("/api/water")
    @jwt_required()
    def water_today():
        u = current_user()
        today = date.today()
        total = sum(w.amount_ml for w in WaterLog.query.filter_by(user_id=u.id, date=today).all())
        return {"amount_ml": total, "target_ml": u.daily_water_target_ml, "date": today.isoformat()}

    @app.post("/api/water")
    @jwt_required()
    def add_water():
        u = current_user()
        data = request.get_json(force=True)
        amt = int(data["amount_ml"])
        w = WaterLog(user_id=u.id, amount_ml=amt, date=date.today())
        db.session.add(w)
        db.session.commit()
        total = sum(x.amount_ml for x in WaterLog.query.filter_by(user_id=u.id, date=date.today()).all())
        return {"amount_ml": total}

    @app.delete("/api/water")
    @jwt_required()
    def clear_water():
        u = current_user()
        WaterLog.query.filter_by(user_id=u.id, date=date.today()).delete()
        db.session.commit()
        return {"ok": True}

    # -------- DAILY CHECK-IN --------
    @app.get("/api/checkins/daily/today")
    @jwt_required()
    def daily_today():
        u = current_user()
        today = date.today()
        c = DailyCheckin.query.filter_by(user_id=u.id, date=today).first()
        if not c:
            return {"submitted": False}
        return {
            "submitted": True,
            "data": {
                "weight_kg": c.weight_kg, "proud_1": c.proud_1, "proud_2": c.proud_2, "proud_3": c.proud_3,
                "sleep_quality": c.sleep_quality, "nutrition_adherence": c.nutrition_adherence,
                "trained_today": c.trained_today, "notes": c.notes,
                "submitted_at": c.submitted_at.isoformat(),
            }
        }

    @app.post("/api/checkins/daily")
    @jwt_required()
    def submit_daily():
        u = current_user()
        today = date.today()
        if DailyCheckin.query.filter_by(user_id=u.id, date=today).first():
            return {"error": "Already submitted today"}, 400
        data = request.get_json(force=True)
        c = DailyCheckin(
            user_id=u.id, date=today,
            weight_kg=float(data.get("weight_kg") or 0) or None,
            proud_1=data.get("proud_1", ""), proud_2=data.get("proud_2", ""), proud_3=data.get("proud_3", ""),
            sleep_quality=int(data.get("sleep_quality", 7)),
            nutrition_adherence=data.get("nutrition_adherence"),
            trained_today=data.get("trained_today"),
            notes=data.get("notes", ""),
        )
        db.session.add(c)

        if c.weight_kg:
            db.session.add(WeightLog(user_id=u.id, weight_kg=c.weight_kg))

        db.session.commit()

        # Ero ack — delivered immediately to the chat
        try:
            ack = generate_daily_acknowledgement(u.id, c)
            db.session.add(ChatMessage(user_id=u.id, role="assistant", content=ack))
            db.session.commit()
        except Exception as e:
            print(f"[ero] daily ack failed: {e}")

        return {"ok": True}

    # -------- WEEKLY CHECK-IN --------
    def _week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())  # Monday

    @app.get("/api/checkins/weekly/available")
    @jwt_required()
    def weekly_available():
        u = current_user()
        ws = _week_start(date.today())
        existing = WeeklyCheckin.query.filter_by(user_id=u.id, week_start_date=ws).first()
        return {
            "available": existing is None,
            "week_start_date": ws.isoformat(),
            "submitted": existing is not None,
        }

    @app.get("/api/checkins/weekly")
    @jwt_required()
    def list_weekly():
        u = current_user()
        rows = WeeklyCheckin.query.filter_by(user_id=u.id).order_by(WeeklyCheckin.week_start_date.desc()).all()
        return [_serialize_weekly(w) for w in rows]

    def _serialize_weekly(w: WeeklyCheckin) -> dict:
        photos = ProgressPhoto.query.filter_by(weekly_checkin_id=w.id).all()
        return {
            "id": w.id, "week_start_date": w.week_start_date.isoformat(),
            "weight_kg": w.weight_kg,
            "nutrition_review": w.nutrition_review, "diet_changes": w.diet_changes,
            "training_review": w.training_review, "performance_improved": w.performance_improved,
            "could_do_better": w.could_do_better, "proud_of": w.proud_of, "main_goal": w.main_goal,
            "sleep_hours": w.sleep_hours, "sleep_quality": w.sleep_quality,
            "support_needed": w.support_needed,
            "energy": w.energy, "fatigue": w.fatigue, "digestion": w.digestion,
            "hunger": w.hunger, "recovery": w.recovery,
            "submitted_at": w.submitted_at.isoformat() if w.submitted_at else None,
            "ero_response": w.ero_response,
            "ero_response_at": w.ero_response_at.isoformat() if w.ero_response_at else None,
            "photos": [{"type": p.photo_type, "url": p.cloudinary_url} for p in photos],
        }

    @app.post("/api/checkins/weekly")
    @jwt_required()
    def submit_weekly():
        u = current_user()
        ws = _week_start(date.today())
        if WeeklyCheckin.query.filter_by(user_id=u.id, week_start_date=ws).first():
            return {"error": "Weekly already submitted"}, 400
        data = request.get_json(force=True)
        w = WeeklyCheckin(
            user_id=u.id, week_start_date=ws,
            weight_kg=float(data.get("weight_kg") or 0) or None,
            nutrition_review=data.get("nutrition_review", ""),
            diet_changes=data.get("diet_changes", ""),
            training_review=data.get("training_review", ""),
            performance_improved=data.get("performance_improved"),
            could_do_better=data.get("could_do_better", ""),
            proud_of=data.get("proud_of", ""),
            main_goal=data.get("main_goal", ""),
            sleep_hours=float(data.get("sleep_hours") or 0) or None,
            sleep_quality=data.get("sleep_quality", ""),
            support_needed=data.get("support_needed", ""),
            energy=int(data.get("energy", 5)),
            fatigue=int(data.get("fatigue", 5)),
            digestion=int(data.get("digestion", 5)),
            hunger=int(data.get("hunger", 5)),
            recovery=int(data.get("recovery", 5)),
        )
        # Schedule Ero's detailed response 1-8 hours later
        w.ero_response_scheduled_at = datetime.utcnow() + timedelta(seconds=random.randint(3600, 28800))
        db.session.add(w)

        if w.weight_kg:
            db.session.add(WeightLog(user_id=u.id, weight_kg=w.weight_kg))

        db.session.commit()

        # Attach any uploaded photo ids if provided
        photo_ids = data.get("photo_ids") or []
        for pid in photo_ids:
            p = ProgressPhoto.query.filter_by(id=pid, user_id=u.id).first()
            if p:
                p.weekly_checkin_id = w.id
        db.session.commit()

        return {"id": w.id, "ero_response_scheduled_at": w.ero_response_scheduled_at.isoformat()}

    @app.post("/api/checkins/weekly/process-pending")
    @jwt_required()
    def process_pending_weekly():
        """Called by frontend on app load — generates any due Ero responses."""
        u = current_user()
        now = datetime.utcnow()
        pending = WeeklyCheckin.query.filter(
            WeeklyCheckin.user_id == u.id,
            WeeklyCheckin.ero_response == "",
            WeeklyCheckin.ero_response_scheduled_at != None,
            WeeklyCheckin.ero_response_scheduled_at <= now,
        ).all()
        delivered = 0
        for w in pending:
            try:
                response = generate_weekly_response(u.id, w)
                w.ero_response = response
                w.ero_response_at = datetime.utcnow()
                db.session.add(ChatMessage(user_id=u.id, role="assistant", content=response))
                db.session.commit()
                delivered += 1
            except Exception as e:
                print(f"[ero] weekly response failed for #{w.id}: {e}")
        return {"delivered": delivered}

    # -------- PHOTOS --------
    @app.post("/api/photos/upload")
    @jwt_required()
    def upload_photo():
        u = current_user()
        if not Config.CLOUDINARY_CLOUD_NAME:
            return {"error": "Cloudinary not configured"}, 500
        photo_type = request.form.get("photo_type", "front")
        f = request.files.get("file")
        if not f:
            return {"error": "No file uploaded"}, 400
        result = cloudinary.uploader.upload(f, folder=f"blake/progress/{photo_type}")
        p = ProgressPhoto(
            user_id=u.id, photo_type=photo_type,
            cloudinary_url=result["secure_url"],
        )
        db.session.add(p)
        db.session.commit()
        return {"id": p.id, "url": p.cloudinary_url, "photo_type": p.photo_type}

    @app.get("/api/photos")
    @jwt_required()
    def list_photos():
        u = current_user()
        # group by weekly check-in
        weeklies = WeeklyCheckin.query.filter_by(user_id=u.id).order_by(WeeklyCheckin.week_start_date.desc()).all()
        out = []
        for w in weeklies:
            ps = ProgressPhoto.query.filter_by(weekly_checkin_id=w.id).all()
            if ps:
                out.append({
                    "week_start_date": w.week_start_date.isoformat(),
                    "weekly_checkin_id": w.id,
                    "photos": [{"type": p.photo_type, "url": p.cloudinary_url} for p in ps],
                })
        return out

    # -------- CHAT --------
    @app.get("/api/chat")
    @jwt_required()
    def list_chat():
        u = current_user()
        rows = ChatMessage.query.filter_by(user_id=u.id).order_by(ChatMessage.created_at.asc()).all()
        return [{"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at.isoformat()} for r in rows]

    @app.post("/api/chat")
    @jwt_required()
    def send_chat():
        u = current_user()
        data = request.get_json(force=True)
        content = (data.get("content") or "").strip()
        image_url = data.get("image_url")  # optional Cloudinary URL
        if not content and not image_url:
            return {"error": "empty"}, 400

        # If there's an image attached, embed a marker in the saved user message
        saved_user_content = content
        if image_url:
            saved_user_content = (content + "\n" if content else "") + f"[image] {image_url}"

        user_msg = ChatMessage(user_id=u.id, role="user", content=saved_user_content)
        db.session.add(user_msg)
        db.session.commit()

        history_rows = (ChatMessage.query.filter_by(user_id=u.id)
                        .order_by(ChatMessage.created_at.asc()).limit(40).all())
        history = [{"role": r.role, "content": r.content} for r in history_rows[:-1]]

        try:
            if image_url:
                reply = chat_with_ero_multimodal(u.id, history, content, image_url=image_url)
            else:
                reply = chat_with_ero(u.id, history, content)
        except Exception as e:
            reply = f"(Ero had trouble responding: {e})"

        a = ChatMessage(user_id=u.id, role="assistant", content=reply)
        db.session.add(a)
        db.session.commit()
        return {
            "user_message": {"id": user_msg.id, "role": "user", "content": saved_user_content, "created_at": user_msg.created_at.isoformat()},
            "assistant_message": {"id": a.id, "role": "assistant", "content": reply, "created_at": a.created_at.isoformat()},
        }

    @app.post("/api/chat/image-upload")
    @jwt_required()
    def chat_image_upload():
        if not Config.CLOUDINARY_CLOUD_NAME:
            return {"error": "Cloudinary not configured"}, 500
        f = request.files.get("file")
        if not f:
            return {"error": "No file uploaded"}, 400
        result = cloudinary.uploader.upload(f, folder="blake/chat")
        return {"url": result["secure_url"]}

    @app.post("/api/chat/proactive-check")
    @jwt_required()
    def chat_proactive_check():
        u = current_user()
        text = proactive_check(u.id)
        return {"delivered": bool(text), "content": text}

    # -------- EXPORT --------
    @app.get("/api/export")
    @jwt_required()
    def export_data():
        u = current_user()
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "weights": [{"weight_kg": w.weight_kg, "logged_at": w.logged_at.isoformat()}
                        for w in WeightLog.query.filter_by(user_id=u.id).all()],
            "sessions": [serialize_session(s) for s in WorkoutSession.query.filter_by(user_id=u.id).all()],
            "meals": [{"id": m.id, "name": m.name, "scheduled_time": m.scheduled_time,
                       "calories": m.calories, "protein": m.protein, "carbs": m.carbs, "fat": m.fat}
                      for m in Meal.query.filter_by(user_id=u.id).all()],
            "daily_checkins": [{
                "date": c.date.isoformat(), "weight_kg": c.weight_kg,
                "proud": [c.proud_1, c.proud_2, c.proud_3],
                "sleep_quality": c.sleep_quality, "nutrition_adherence": c.nutrition_adherence,
                "trained_today": c.trained_today, "notes": c.notes,
            } for c in DailyCheckin.query.filter_by(user_id=u.id).all()],
            "weekly_checkins": [_serialize_weekly(w) for w in WeeklyCheckin.query.filter_by(user_id=u.id).all()],
        }
        return jsonify(data)


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
