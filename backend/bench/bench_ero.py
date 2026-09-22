"""Bench-test Ero against seeded, realistic data.

Usage (from backend/):  python bench/bench_ero.py [scenario names...]
Writes a transcript to bench/results/<timestamp>.md for review. Costs real API calls.
Uses its own SQLite file so it never touches a real database.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(HERE, "bench.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")
os.environ.setdefault("BLAKE_PASSWORD", "bench")
os.environ["FRONTEND_ORIGIN"] = "*"

from app import app, update_previous_from_session  # noqa: E402
from extensions import db  # noqa: E402
from models import (  # noqa: E402
    DailyCheckin, ExercisePrevious, Meal, MealLog, User, WeeklyCheckin, WeightLog, WorkoutSession, WorkoutSet,
)
from program import DAY_TO_SESSION, PROGRAM  # noqa: E402
import ero  # noqa: E402

TODAY = date.today()


def _session(uid, day, stype, lifts, completed=True, hour=18):
    s = WorkoutSession(user_id=uid, session_type=stype,
                       started_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=hour, minutes=30),
                       completed_at=(datetime.combine(day, datetime.min.time()) + timedelta(hours=hour + 1, minutes=25)) if completed else None)
    db.session.add(s)
    db.session.flush()
    n = 0
    for ex, sets in lifts.items():
        for i, (w, r) in enumerate(sets, 1):
            db.session.add(WorkoutSet(session_id=s.id, exercise_name=ex, set_number=i, weight_kg=w, reps=r,
                                      logged_at=s.started_at + timedelta(minutes=5 * n)))
            n += 1
    if completed:
        update_previous_from_session(s)
    return s


def seed(uid: int):
    """Two weeks of believable history ending yesterday, with a Hack Squat stall and a swap."""
    WeightLog.query.filter_by(user_id=uid).delete()  # drop the app's 65.3 auto-seed
    # Bodyweight creeping up, one flat week then a bump
    series = [65.3, 65.3, 65.4, 65.5, 65.4, 65.5, 65.6, 65.6, 65.7, 65.6, 65.7, 65.8, 65.8, 65.9]
    for i, w in enumerate(series):
        d = TODAY - timedelta(days=14 - i)
        db.session.add(WeightLog(user_id=uid, weight_kg=w, logged_at=datetime.combine(d, datetime.min.time()) + timedelta(hours=7)))

    upper = {"Flat DB Bench": [(22.5, 8), (22.5, 8), (22.5, 7), (22.5, 6)], "Pec Deck Fly": [(54.7, 12)] * 3,
             "Lat Pulldown Pronated": [(50, 12), (50, 11), (50, 10)], "Chest Supported T-Bar Row": [(35, 12)] * 3,
             "Seated Shoulder Press": [(56.8, 12), (56.8, 10), (56.8, 9)], "Cable Triceps Pushdown": [(45, 15)] * 3,
             "Standing Bicep Cable Curl": [(50, 15), (50, 13), (50, 13)]}
    lower = {"Leg Extension": [(85, 12), (85, 10), (92.5, 8)], "Seated Leg Curl": [(63, 8), (57, 10), (57, 10)],
             "Hack Squat": [(130, 8), (130, 8), (130, 7)], "Leg Press": [(110, 10), (105, 11), (105, 10)],
             "Calf Raise Machine": [(60, 12)] * 4}
    push = {"Machine Chest Press": [(40, 8), (40, 8), (40, 8)], "Dumbbell Lateral Raise": [(7.5, 15)] * 3,
            "Incline Chest Press": [(45, 10), (45, 8), (45, 10)], "Seated Dumbbell Shoulder Press": [(20, 8), (17.5, 12), (17.5, 12)],
            "Incline Cable Fly": [(32.5, 10)] * 2, "Cable Triceps Pushdown Straight Bar": [(50, 9), (45, 10), (45, 12)],
            "Single Arm Overhead Triceps Cable Extension": [(12.5, 12)] * 3, "Weighted Sit Up": [(10, 12)] * 3}
    pull = {"Lat Pulldown Machine": [(42.5, 10)] * 3, "Chest Supported Row Pronated": [(40, 10), (40, 10), (40, 9)],
            "Single Arm Cable Row": [(25, 10), (20, 12), (20, 12)], "Reverse Pec Deck Fly": [(47, 12), (45, 15), (45, 14)],
            "Preacher Curl": [(36, 12), (36, 10), (30, 12)], "Incline Dumbbell Curl": [(15, 10), (12.5, 12), (12.5, 12)],
            "Ab Wheel Rollout": [(0, 8)] * 3}
    legs = {"Barbell Hip Thrust": [(60, 10), (60, 10), (60, 9)], "Lying Leg Curl": [(50, 12), (50, 11), (50, 11)],
            "Leg Extension": [(85, 12), (77.5, 15), (77.5, 13)], "Hyperextension": [(10, 12)] * 3,
            "Seated Machine Hip Adductor": [(60, 12), (60, 11), (60, 10)], "Standing Calf Raise": [(65, 13), (65, 13), (65, 12), (65, 12)],
            "Cable Kneeling Crunch": [(70, 13), (70, 12), (70, 14), (70, 11)]}
    by_type = {"Upper": upper, "Lower": lower, "Push": push, "Pull": pull, "Legs": legs}

    # Sessions for the last 14 days following the split; one Pull day swapped to Legs; one Lower missed.
    missed_day = None
    for i in range(21, 0, -1):
        d = TODAY - timedelta(days=i)
        sched = DAY_TO_SESSION[d.weekday()]
        if sched == "Rest":
            continue
        if sched == "Push" and 7 < i <= 14 and missed_day is None:
            missed_day = d  # missed once, last week
            db.session.add(DailyCheckin(user_id=uid, date=d, weight_kg=series[max(0, 14 - i)], sleep_quality=5,
                                        nutrition_adherence="Partially", trained_today="No", notes="knackered after work"))
            continue
        actual = "Legs" if (sched == "Pull" and i <= 7) else sched
        lifts = by_type[actual]
        # Earlier week: slightly lighter so there is visible progress except Hack Squat (stalled 3 sessions)
        if i > 7:
            lifts = {ex: [(w - (2.5 if w >= 20 and ex != "Hack Squat" else 0), r) for w, r in sets] for ex, sets in lifts.items()}
        if i > 14:
            lifts = {ex: [(w - (2.5 if w >= 20 and ex != "Hack Squat" else 0), r) for w, r in sets] for ex, sets in lifts.items()}
        _session(uid, d, actual, lifts)
        sleep = 5 if i in (3, 2) else 7
        db.session.add(DailyCheckin(user_id=uid, date=d, weight_kg=series[max(0, 14 - i)], sleep_quality=sleep,
                                    nutrition_adherence="Yes" if i % 3 else "Partially", trained_today="Yes",
                                    proud_1="showed up", proud_2="hit all meals", proud_3="", notes=""))
    # Hack squat in the last Lower session (this week) at the same 130 top weight -> 3 sessions stalled
    db.session.add(WeeklyCheckin(user_id=uid, week_start_date=TODAY - timedelta(days=TODAY.weekday() + 7), weight_kg=65.6,
                                 nutrition_review="mostly on it, missed meal 4 twice", diet_changes="", training_review="all sessions except lower tue",
                                 performance_improved="Partially", could_do_better="sleep", proud_of="hip thrust felt strong",
                                 main_goal="hit every session", sleep_hours=6.5, sleep_quality="patchy", support_needed="",
                                 energy=6, fatigue=6, digestion=7, hunger=7, recovery=5))
    # Today's meals: first three eaten
    for m in Meal.query.filter_by(user_id=uid).order_by(Meal.sort_order).limit(3):
        db.session.add(MealLog(user_id=uid, meal_id=m.id, date=TODAY, eaten=True))
    db.session.commit()


def run(uid, turns, history=None):
    """Run a multi-turn conversation. Returns list of (user, reply, tool_calls)."""
    history = list(history or [])
    out = []
    for msg in turns:
        context = ero.build_context(uid)
        system = ero.ERO_SYSTEM_PROMPT + "\n\n" + context
        final_user = msg + ero._turn_notes(uid, history)
        messages = history + [{"role": "user", "content": final_user}]
        text, calls = ero._run_tool_loop(uid, system, messages)
        out.append((msg, text, calls))
        history += [{"role": "user", "content": msg}, {"role": "assistant", "content": text}]
    return out


def start_active(uid, stype, lifts):
    return _session(uid, TODAY, stype, lifts, completed=False)


def clear_active(uid):
    for s in WorkoutSession.query.filter_by(user_id=uid, completed_at=None).all():
        WorkoutSet.query.filter_by(session_id=s.id).delete()
        db.session.delete(s)
    db.session.commit()


SCENARIOS = {
    "subway": {
        "rubric": "Stays on Subway; compares to Meal 5 (spag bol 729/60P); ONE fix-up; holds position on 'are you sure?'",
        "turns": ["im getting a footlong chicken teriyaki subway on wholegrain, subbing for dinner. thoughts?", "are you sure?", "what would you get if you were me"],
    },
    "overload_rundown": {
        "rubric": "Full list of ALL exercises for the active session with target weight+reps from working weights; no exercise from another session; no invented weights.",
        "active": ("Push", {}),
        "turns": ["what should i do today", "what about bench"],
    },
    "mid_session": {
        "rubric": "Uses the logged 40x8 x3; gives a clear next-session call (+2.5/+5kg or reps); short.",
        "active": ("Push", {"Machine Chest Press": [(40, 8), (40, 8), (40, 8)]}),
        "turns": ["chest press done 40 for 8 8 8, felt easy. next?"],
    },
    "conviction": {
        "rubric": "Takes a side on face pulls; same side on 'if you had to pick'; no reversal.",
        "turns": ["would adding face pulls to pull day be bad?", "if you had to pick one way?", "really?"],
    },
    "swap_week": {
        "rubric": "Legs on the Pull day counted as trained (SWAPPED), the missed Push called out as the only miss; hack squat stall or sleep flagged if relevant.",
        "turns": ["hows this week looking?"],
    },
    "numbers": {
        "rubric": "Hack Squat quoted exactly from data (130 top); deadlift -> not in program / no logged value, does not invent.",
        "turns": ["what did i hit on hack squat last time", "and deadlift?"],
    },
    "stall": {
        "rubric": "Notices Hack Squat unchanged for 3 sessions; gives ONE concrete move (deload / tempo / technique), not 'keep trying'.",
        "turns": ["how am i going on legs"],
    },
    "meal_change": {
        "rubric": "Shows Before/After/delta math anchored to real food; calls update_meal ONCE with a full macro set; confirms.",
        "turns": ["swap the chicken in meal 3 for tuna, same amount", "yep do it"],
    },
    "weight": {
        "rubric": "Calls log_weight immediately; one line on the trend using real numbers (65.9 latest, +~0.4 wow).",
        "turns": ["weighed in at 66.1 this morning"],
    },
    "sore": {
        "rubric": "Specific, decisive advice; no hedging; ties to program (tomorrow's session from schedule).",
        "turns": ["front delt is a bit sore after push, should i still train tomorrow?"],
    },
    "sleep": {
        "rubric": "Connects 5h sleep to expected performance; still trains; adjusts expectations concretely.",
        "turns": ["only got 5 hours sleep, got upper tonight"],
    },
    "cbf": {
        "rubric": "Pushes back, redirects, no lecture, no guilt trip, specific.",
        "turns": ["cbf going tonight"],
    },
    "personal": {
        "rubric": "One sentence acknowledgement, then redirect to training/recovery. No therapy.",
        "turns": ["me and my girlfriend had a massive fight, head's not in it"],
    },
    "snack": {
        "rubric": "Anchors to the plan (Muscle Nation bar is already in Meal 2); specific yes/no with macros from the plan.",
        "turns": ["is a muscle nation bar fine as a snack at work"],
    },
    "correction": {
        "rubric": "After being corrected to Upper, answers for Upper immediately without arguing or re-asserting Push.",
        "turns": ["what's my top lift target today", "nah im doing upper today not push"],
    },
    "general": {
        "rubric": "Any-topic PT answer: creatine timing - short, correct, no hedging, ties to his 5g/day.",
        "turns": ["does it matter when i take creatine"],
    },
    "tomorrow": {
        "rubric": "Correct weekday/session for tomorrow and the day after from the SCHEDULE block; no arithmetic slips.",
        "turns": ["whats tomorrow and the day after", "and whens my next legs day"],
    },
    "weekly": {"special": "weekly", "rubric": "Four sections; exact weight change; names the Hack Squat stall and the missed Push; per-day plan with real target weights; one commitment; tools used only if macros need changing."},
    "daily_ack": {"special": "daily", "rubric": "1-2 sentences, references something specific from the check-in, casual."},
}


def main():
    names = sys.argv[1:] or list(SCENARIOS)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out_path = os.path.join(HERE, "results", datetime.now().strftime("%Y%m%d-%H%M%S") + ".md")
    lines = [f"# Ero bench {datetime.now():%Y-%m-%d %H:%M}", ""]
    with app.app_context():
        user = User.query.filter_by(username="blake").first()
        seed(user.id)
        for name in names:
            sc = SCENARIOS[name]
            clear_active(user.id)
            if sc.get("active"):
                start_active(user.id, *sc["active"])
                db.session.commit()
            lines += [f"## {name}", f"_Rubric: {sc['rubric']}_", ""]
            print(f"[{name}] ...", flush=True)
            try:
                if sc.get("special") == "weekly":
                    wk = WeeklyCheckin(user_id=user.id, week_start_date=TODAY - timedelta(days=TODAY.weekday()), weight_kg=65.9,
                                       nutrition_review="hit everything except meal 4 on mon, work got busy", diet_changes="sick of spag bol tbh",
                                       training_review="did everything, swapped pull for legs friday cause mate wanted to train legs",
                                       performance_improved="Yes", could_do_better="sleep, two nights under 6", proud_of="db bench felt strong, all sets",
                                       main_goal="break the hack squat plateau", sleep_hours=6.5, sleep_quality="patchy",
                                       support_needed="what to do about hack squat", energy=6, fatigue=6, digestion=7, hunger=8, recovery=5)
                    db.session.add(wk)
                    db.session.commit()
                    reply = ero.generate_weekly_response(user.id, wk)
                    lines += ["**Weekly check-in submitted (see seed).**", "", f"**Ero:** {reply}", ""]
                    for m in Meal.query.filter_by(user_id=user.id, is_active=True).order_by(Meal.sort_order):
                        lines.append(f"> meal now: {m.name} [{m.calories}/{m.protein}/{m.carbs}/{m.fat}]")
                    lines.append("")
                elif sc.get("special") == "daily":
                    dc = DailyCheckin(user_id=user.id, date=TODAY, weight_kg=66.0, proud_1="hit hack squat 130 for 8 8 8 finally", proud_2="no maccas",
                                      proud_3="", sleep_quality=6, nutrition_adherence="Yes", trained_today="Yes", notes="knee felt a bit clicky on leg press")
                    db.session.add(dc)
                    db.session.commit()
                    reply = ero.generate_daily_acknowledgement(user.id, dc)
                    lines += ["**Daily check-in submitted (see seed).**", "", f"**Ero:** {reply}", ""]
                    db.session.delete(dc)
                    db.session.commit()
                else:
                  for msg, reply, calls in run(user.id, sc["turns"]):
                    lines += [f"**Blake:** {msg}", "", f"**Ero:** {reply}", ""]
                    for c in calls:
                        lines += [f"> tool `{c['name']}` {json.dumps(c['input'])} -> {json.dumps(c['result'])[:240]}", ""]
            except Exception as e:  # keep going, report
                lines += [f"**ERROR:** {e}", ""]
            lines.append("---")
            lines.append("")
        clear_active(user.id)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
