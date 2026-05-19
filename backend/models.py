from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    daily_calorie_target = db.Column(db.Integer, default=3388)
    daily_protein_target = db.Column(db.Integer, default=229)
    daily_carb_target = db.Column(db.Integer, default=414)
    daily_fat_target = db.Column(db.Integer, default=82)
    daily_water_target_ml = db.Column(db.Integer, default=3000)
    goal_weight_kg = db.Column(db.Float, default=70.0)
    starting_weight_kg = db.Column(db.Float, default=65.3)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)


class WeightLog(db.Model):
    __tablename__ = "weight_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkoutSession(db.Model):
    __tablename__ = "workout_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_type = db.Column(db.String(32), nullable=False)  # Upper, Lower, Push, Pull, Legs
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, default="")
    difficulty = db.Column(db.Integer, nullable=True)  # 1–10 user-rated

    sets = db.relationship(
        "WorkoutSet", backref="session", cascade="all, delete-orphan", lazy="select"
    )


class WorkoutSet(db.Model):
    __tablename__ = "workout_sets"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("workout_sessions.id"), nullable=False)
    exercise_name = db.Column(db.String(128), nullable=False)
    set_number = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    rpe = db.Column(db.Float, nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)


class Meal(db.Model):
    __tablename__ = "meals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    scheduled_time = db.Column(db.String(16))  # e.g. "08:30"
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Integer, default=0)
    carbs = db.Column(db.Integer, default=0)
    fat = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class MealLog(db.Model):
    __tablename__ = "meal_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey("meals.id"), nullable=False)
    date = db.Column(db.Date, default=date.today, index=True)
    eaten = db.Column(db.Boolean, default=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)


class WaterLog(db.Model):
    __tablename__ = "water_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount_ml = db.Column(db.Integer, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=date.today, index=True)


class DailyCheckin(db.Model):
    __tablename__ = "daily_checkins"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today, index=True)
    weight_kg = db.Column(db.Float)
    proud_1 = db.Column(db.Text, default="")
    proud_2 = db.Column(db.Text, default="")
    proud_3 = db.Column(db.Text, default="")
    sleep_quality = db.Column(db.Integer, default=7)
    nutrition_adherence = db.Column(db.String(16))  # Yes / Partially / No
    trained_today = db.Column(db.String(16))  # Yes / No / Rest Day
    notes = db.Column(db.Text, default="")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class WeeklyCheckin(db.Model):
    __tablename__ = "weekly_checkins"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    week_start_date = db.Column(db.Date, index=True)
    weight_kg = db.Column(db.Float)
    nutrition_review = db.Column(db.Text, default="")
    diet_changes = db.Column(db.Text, default="")
    training_review = db.Column(db.Text, default="")
    performance_improved = db.Column(db.String(32))
    could_do_better = db.Column(db.Text, default="")
    proud_of = db.Column(db.Text, default="")
    main_goal = db.Column(db.Text, default="")
    sleep_hours = db.Column(db.Float)
    sleep_quality = db.Column(db.Text, default="")
    support_needed = db.Column(db.Text, default="")
    energy = db.Column(db.Integer)
    fatigue = db.Column(db.Integer)
    digestion = db.Column(db.Integer)
    hunger = db.Column(db.Integer)
    recovery = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ero_response = db.Column(db.Text, default="")
    ero_response_at = db.Column(db.DateTime, nullable=True)
    ero_response_scheduled_at = db.Column(db.DateTime, nullable=True)

    photos = db.relationship("ProgressPhoto", backref="checkin", lazy="select")


class ProgressPhoto(db.Model):
    __tablename__ = "progress_photos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weekly_checkin_id = db.Column(db.Integer, db.ForeignKey("weekly_checkins.id"), nullable=True)
    photo_type = db.Column(db.String(16))  # front / side / back
    cloudinary_url = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # user / assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class ExercisePrevious(db.Model):
    """Stores most-recent logged weights per exercise per session_type for the preview-above-input feature."""
    __tablename__ = "exercise_previous"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_type = db.Column(db.String(32), nullable=False)
    exercise_name = db.Column(db.String(128), nullable=False)
    sets_json = db.Column(db.Text, nullable=False)  # JSON list of {weight_kg, reps}
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "session_type", "exercise_name", name="uix_prev_exercise"),
    )
