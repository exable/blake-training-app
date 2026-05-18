"""Ero AI helper — context building + Anthropic API calls."""
import os
import json
from datetime import date, datetime, timedelta
from anthropic import Anthropic
from extensions import db
from models import (
    WeightLog, WorkoutSession, WorkoutSet, MealLog, Meal,
    DailyCheckin, WeeklyCheckin, WaterLog, ExercisePrevious,
)
from program import ERO_SYSTEM_PROMPT, PROGRAM, DAY_TO_SESSION
from config import Config


def _client():
    if not Config.ANTHROPIC_API_KEY:
        return None
    return Anthropic(api_key=Config.ANTHROPIC_API_KEY)


def _format_program() -> str:
    lines = []
    for stype, exs in PROGRAM.items():
        lines.append(f"  {stype}:")
        for ex in exs:
            rpe = f" @ RPE {ex['rpe']}" if ex.get("rpe") else ""
            lines.append(f"    - {ex['name']}: {ex['sets']}×{ex['rep_range']}{rpe}, {ex['rest']}s rest")
    return "\n".join(lines)


def _format_working_weights(user_id: int) -> str:
    rows = ExercisePrevious.query.filter_by(user_id=user_id).all()
    if not rows:
        return "  (none logged yet)"
    by_session: dict[str, list[str]] = {}
    for r in rows:
        sets = json.loads(r.sets_json)
        summary = ", ".join(f"{s['weight_kg']}kg×{s['reps']}" for s in sets)
        by_session.setdefault(r.session_type, []).append(f"    {r.exercise_name}: {summary}")
    out = []
    for stype, lines in by_session.items():
        out.append(f"  {stype}:")
        out.extend(lines)
    return "\n".join(out)


def build_context(user_id: int) -> str:
    """Build a concise data-rich context block to prepend to Ero conversations."""
    today = date.today()
    seven_days_ago = today - timedelta(days=14)

    # weights
    weights = (WeightLog.query
               .filter(WeightLog.user_id == user_id)
               .order_by(WeightLog.logged_at.desc())
               .limit(10).all())
    weight_lines = [f"{w.logged_at.strftime('%Y-%m-%d')}: {w.weight_kg}kg" for w in weights]

    # recent sessions
    sessions = (WorkoutSession.query
                .filter(WorkoutSession.user_id == user_id,
                        WorkoutSession.started_at >= datetime.combine(seven_days_ago, datetime.min.time()))
                .order_by(WorkoutSession.started_at.desc())
                .limit(6).all())
    session_lines = []
    for s in sessions:
        sets = WorkoutSet.query.filter_by(session_id=s.id).order_by(WorkoutSet.id.asc()).all()
        by_ex = {}
        for st in sets:
            by_ex.setdefault(st.exercise_name, []).append(f"{st.weight_kg}kg×{st.reps}")
        lines = "; ".join(f"{n}: {', '.join(v)}" for n, v in by_ex.items())
        session_lines.append(f"{s.started_at.strftime('%Y-%m-%d')} {s.session_type} — {lines}")

    # today's nutrition adherence
    today_logs = MealLog.query.filter_by(user_id=user_id, date=today).all()
    eaten_count = sum(1 for ml in today_logs if ml.eaten)
    total_meals = Meal.query.filter_by(user_id=user_id, is_active=True).count()

    # water today
    water_today = sum(w.amount_ml for w in WaterLog.query.filter_by(user_id=user_id, date=today).all())

    # last 7 daily checkins
    dailies = (DailyCheckin.query
               .filter(DailyCheckin.user_id == user_id,
                       DailyCheckin.date >= seven_days_ago)
               .order_by(DailyCheckin.date.desc()).all())
    daily_lines = [
        f"{d.date} weight={d.weight_kg}kg sleep={d.sleep_quality}/10 nutrition={d.nutrition_adherence} trained={d.trained_today}"
        for d in dailies
    ]

    # latest weekly
    weekly = (WeeklyCheckin.query.filter_by(user_id=user_id)
              .order_by(WeeklyCheckin.week_start_date.desc()).first())
    weekly_block = ""
    if weekly:
        weekly_block = (
            f"\nLatest weekly check-in ({weekly.week_start_date}):\n"
            f"  weight: {weekly.weight_kg}kg\n"
            f"  nutrition review: {weekly.nutrition_review}\n"
            f"  training review: {weekly.training_review}\n"
            f"  performance improved: {weekly.performance_improved}\n"
            f"  main goal: {weekly.main_goal}\n"
            f"  energy/fatigue/digestion/hunger/recovery: "
            f"{weekly.energy}/{weekly.fatigue}/{weekly.digestion}/{weekly.hunger}/{weekly.recovery}\n"
        )

    today_session = DAY_TO_SESSION[today.weekday()]

    ctx = f"""[BLAKE'S LIVE DATA — {today} ({today.strftime('%A')}, scheduled: {today_session})]

CURRENT PROGRAM (ULPPL — rest Wed & Sun):
{_format_program()}

CURRENT WORKING WEIGHTS (most recent logged sets per exercise):
{_format_working_weights(user_id)}

Recent bodyweight entries:
{chr(10).join('  ' + w for w in weight_lines) if weight_lines else '  (none)'}

Recent completed workouts (last 14 days):
{chr(10).join('  ' + s for s in session_lines) if session_lines else '  (none)'}

Today's nutrition: {eaten_count}/{total_meals} meals eaten, {water_today}ml water
Recent daily check-ins:
{chr(10).join('  ' + d for d in daily_lines) if daily_lines else '  (none)'}
{weekly_block}
"""
    return ctx


def chat_with_ero(user_id: int, history: list[dict], user_message: str) -> str:
    """Send a chat message and return Ero's reply. history is a list of {role, content}."""
    client = _client()
    if not client:
        return "(Ero is offline — ANTHROPIC_API_KEY not configured.)"

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    messages = list(history) + [{"role": "user", "content": user_message}]

    resp = client.messages.create(
        model=Config.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


def generate_weekly_response(user_id: int, weekly: WeeklyCheckin) -> str:
    client = _client()
    if not client:
        return "(Ero is offline — ANTHROPIC_API_KEY not configured.)"

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    checkin_summary = json.dumps({
        "week_start_date": str(weekly.week_start_date),
        "weight_kg": weekly.weight_kg,
        "nutrition_review": weekly.nutrition_review,
        "diet_changes": weekly.diet_changes,
        "training_review": weekly.training_review,
        "performance_improved": weekly.performance_improved,
        "could_do_better": weekly.could_do_better,
        "proud_of": weekly.proud_of,
        "main_goal": weekly.main_goal,
        "sleep_hours": weekly.sleep_hours,
        "sleep_quality": weekly.sleep_quality,
        "support_needed": weekly.support_needed,
        "energy": weekly.energy,
        "fatigue": weekly.fatigue,
        "digestion": weekly.digestion,
        "hunger": weekly.hunger,
        "recovery": weekly.recovery,
    }, indent=2)

    prompt = (
        "Blake just submitted his weekly check-in. Read his actual numbers, recent training log, "
        "weight trend, and his answers below. Give him a thorough, personalised response — "
        "reference specific lifts, specific weights, the actual weight change, his actual answers. "
        "Address every section of his check-in. Tie everything back to his lean-bulk goal (70kg). "
        "Casual tone, use 'man'/'bro'/'g' naturally. No fluff, no generic advice.\n\n"
        f"His weekly check-in answers:\n{checkin_summary}"
    )

    resp = client.messages.create(
        model=Config.ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


def generate_daily_acknowledgement(user_id: int, checkin: DailyCheckin) -> str:
    client = _client()
    if not client:
        return "Locked in. Keep stacking days, g."

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    prompt = (
        "Blake just submitted his daily check-in. Drop a SHORT (1-2 sentence) encouraging "
        "acknowledgement. Reference one specific thing he wrote if it stands out. Casual. "
        f"Today's check-in: weight={checkin.weight_kg}kg, sleep={checkin.sleep_quality}/10, "
        f"nutrition={checkin.nutrition_adherence}, trained={checkin.trained_today}, "
        f"proud: '{checkin.proud_1}', '{checkin.proud_2}', '{checkin.proud_3}', "
        f"notes: '{checkin.notes}'"
    )

    resp = client.messages.create(
        model=Config.ANTHROPIC_MODEL,
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
