"""Ero AI helper — context building + Anthropic API calls."""
import os
import json
from datetime import date, datetime, timedelta
from anthropic import Anthropic
from extensions import db
from models import (
    User, WeightLog, WorkoutSession, WorkoutSet, MealLog, Meal,
    DailyCheckin, WeeklyCheckin, WaterLog, ExercisePrevious, ChatMessage,
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


def _format_weight_trend(user_id: int) -> str:
    """7d / 14d rolling avg + week-over-week delta."""
    today = date.today()
    rows = (WeightLog.query.filter_by(user_id=user_id)
            .order_by(WeightLog.logged_at.desc()).all())
    if not rows:
        return "  (no bodyweight logged yet)"

    def avg_window(days: int):
        cutoff = datetime.utcnow() - timedelta(days=days)
        window = [r.weight_kg for r in rows if r.logged_at >= cutoff]
        return sum(window) / len(window) if window else None

    latest = rows[0].weight_kg
    earliest = rows[-1].weight_kg
    a7 = avg_window(7)
    a14 = avg_window(14)

    # Week-over-week: avg of last 7 days vs avg of the 7 days before that
    prev_window = [r.weight_kg for r in rows
                   if timedelta(days=7) <= (datetime.utcnow() - r.logged_at) <= timedelta(days=14)]
    prev_avg = sum(prev_window) / len(prev_window) if prev_window else None
    wow_delta = (a7 - prev_avg) if (a7 is not None and prev_avg is not None) else None

    # Has weight been stuck for a full week?
    week_window = [r.weight_kg for r in rows if (datetime.utcnow() - r.logged_at) <= timedelta(days=8)]
    week_range = (max(week_window) - min(week_window)) if len(week_window) >= 3 else None
    stuck = (week_range is not None and week_range < 0.4 and len(week_window) >= 3)

    parts = [f"  latest: {latest}kg",
             f"earliest logged: {earliest}kg"]
    if a7 is not None: parts.append(f"7d avg: {a7:.2f}kg")
    if a14 is not None: parts.append(f"14d avg: {a14:.2f}kg")
    if wow_delta is not None:
        sign = "+" if wow_delta >= 0 else ""
        parts.append(f"week-over-week: {sign}{wow_delta:.2f}kg")
    if stuck:
        parts.append("⚠ STALLED (no movement >0.4kg over last week)")
    return "  " + " · ".join(parts)


def _format_schedule_adherence(user_id: int) -> str:
    """Last 14 days: scheduled session vs trained_today answer + actual workout existence."""
    today = date.today()
    out = []
    sessions_by_date: dict = {}
    sessions = (WorkoutSession.query.filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.started_at >= datetime.combine(today - timedelta(days=14), datetime.min.time()),
    ).all())
    for s in sessions:
        sessions_by_date.setdefault(s.started_at.date(), []).append(s)

    dailies = {c.date: c for c in DailyCheckin.query.filter(
        DailyCheckin.user_id == user_id,
        DailyCheckin.date >= today - timedelta(days=14),
    ).all()}

    missed = 0
    trained = 0
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        scheduled = DAY_TO_SESSION_BY_NAME(d.weekday())
        completed = any(s.completed_at for s in sessions_by_date.get(d, []))
        daily_ans = dailies.get(d)
        ans = daily_ans.trained_today if daily_ans else None

        marker = "·"
        if scheduled == "Rest":
            marker = "💤"
        elif completed:
            marker = "✓"; trained += 1
        elif ans == "Yes":
            marker = "?"  # said yes but no session logged
        elif ans in ("No", None):
            if scheduled != "Rest":
                marker = "✗"; missed += 1

        out.append(f"{d.strftime('%a %d')}: {scheduled} {marker}")

    summary = f"  Last 14 days — trained: {trained}, missed: {missed}"
    return summary + "\n  " + "\n  ".join(out)


def DAY_TO_SESSION_BY_NAME(weekday: int) -> str:
    return DAY_TO_SESSION[weekday]


def _format_stalls(user_id: int) -> str:
    """Detect exercises whose top working weight hasn't moved in the last 2-3 logged sessions."""
    out = []
    # Pull all sets in last 60 days, group by exercise
    cutoff = datetime.utcnow() - timedelta(days=60)
    rows = (db.session.query(WorkoutSet, WorkoutSession)
            .join(WorkoutSession, WorkoutSession.id == WorkoutSet.session_id)
            .filter(WorkoutSession.user_id == user_id,
                    WorkoutSet.logged_at >= cutoff)
            .order_by(WorkoutSet.logged_at.asc()).all())
    by_ex: dict[str, list] = {}
    for st, sess in rows:
        if st.weight_kg <= 0:
            continue  # skip cardio / bodyweight markers
        by_ex.setdefault(st.exercise_name, []).append((sess.started_at, st.weight_kg, st.reps))

    for ex, entries in by_ex.items():
        # Compute top weight per distinct session date
        by_session_top: dict = {}
        for ts, wt, reps in entries:
            d = ts.date()
            by_session_top[d] = max(by_session_top.get(d, 0), wt)
        sessions_sorted = sorted(by_session_top.items())
        if len(sessions_sorted) < 2:
            continue
        last_two = [w for _, w in sessions_sorted[-3:]]  # last 2-3 session top weights
        if len(set(last_two)) == 1 and len(last_two) >= 2:
            out.append(f"  {ex}: stalled at {last_two[-1]}kg over last {len(last_two)} sessions")

    return "\n".join(out) if out else "  (no stalls detected)"


def _format_recent_prs(user_id: int) -> str:
    """Detect recent top-weight increases in last 14 days."""
    out = []
    cutoff = datetime.utcnow() - timedelta(days=14)
    rows = (db.session.query(WorkoutSet, WorkoutSession)
            .join(WorkoutSession, WorkoutSession.id == WorkoutSet.session_id)
            .filter(WorkoutSession.user_id == user_id,
                    WorkoutSet.logged_at >= cutoff)
            .order_by(WorkoutSet.logged_at.asc()).all())
    by_ex: dict[str, list] = {}
    for st, sess in rows:
        if st.weight_kg <= 0:
            continue
        by_ex.setdefault(st.exercise_name, []).append((sess.started_at, st.weight_kg))
    for ex, entries in by_ex.items():
        entries_sorted = sorted(entries)
        max_w = max(w for _, w in entries_sorted)
        latest = entries_sorted[-1]
        if latest[1] == max_w and len([w for _, w in entries_sorted if w == max_w]) == 1:
            # First time hitting this weight
            out.append(f"  {ex}: new top {latest[1]}kg ({latest[0].strftime('%a %d %b')})")
    return "\n".join(out) if out else "  (no new top weights in last 14d)"


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


def _format_meal_plan(user_id: int, today: date) -> str:
    meals = Meal.query.filter_by(user_id=user_id, is_active=True).order_by(Meal.sort_order.asc()).all()
    if not meals:
        return "  (no meals configured)"
    logs = {ml.meal_id: ml.eaten for ml in MealLog.query.filter_by(user_id=user_id, date=today).all()}
    lines = []
    total_kcal = total_p = total_c = total_f = 0
    for m in meals:
        total_kcal += m.calories or 0
        total_p += m.protein or 0
        total_c += m.carbs or 0
        total_f += m.fat or 0
        status = "EATEN" if logs.get(m.id) else "not eaten"
        lines.append(
            f"    {m.scheduled_time or '--:--'} — {m.name} "
            f"[{m.calories}kcal / {m.protein}P / {m.carbs}C / {m.fat}F] — {status}"
        )
    lines.append(
        f"  PLAN TOTALS (when all eaten): {total_kcal}kcal / {total_p}P / {total_c}C / {total_f}F"
    )
    return "\n".join(lines)


def _format_targets(u: User) -> str:
    return (
        f"  Daily targets: {u.daily_calorie_target}kcal / "
        f"{u.daily_protein_target}P / {u.daily_carb_target}C / {u.daily_fat_target}F\n"
        f"  Water target: {u.daily_water_target_ml}ml/day\n"
        f"  Starting weight: {u.starting_weight_kg}kg → Goal: {u.goal_weight_kg}kg (lean bulk)"
    )


def _format_active_session(user_id: int) -> str | None:
    """If there's an in-progress workout, build a high-visibility block describing it.
    Returns None if no session is active."""
    active = (WorkoutSession.query
              .filter(WorkoutSession.user_id == user_id,
                      WorkoutSession.completed_at == None)
              .order_by(WorkoutSession.started_at.desc())
              .first())
    if not active:
        return None

    sets = WorkoutSet.query.filter_by(session_id=active.id).order_by(WorkoutSet.id.asc()).all()
    by_ex: dict[str, list[str]] = {}
    for s in sets:
        # Cardio markers (weight=0, reps<=1) → shown as "done" rather than 0kg×1
        if s.weight_kg == 0 and s.reps <= 1:
            by_ex.setdefault(s.exercise_name, []).append("done (cardio)")
        else:
            by_ex.setdefault(s.exercise_name, []).append(f"{s.weight_kg}kg×{s.reps}")

    program_exs = PROGRAM.get(active.session_type, [])
    prev_lookup = {
        r.exercise_name: json.loads(r.sets_json)
        for r in ExercisePrevious.query.filter_by(
            user_id=user_id, session_type=active.session_type
        ).all()
    }

    lines = []
    for ex in program_exs:
        prev = prev_lookup.get(ex["name"])
        prev_str = ""
        if prev:
            prev_str = " — last time: " + ", ".join(
                f"{p['weight_kg']}kg×{p['reps']}" for p in prev
            )
        rpe = f" @ RPE {ex['rpe']}" if ex.get("rpe") else ""
        cardio = " (cardio)" if ex.get("cardio") else ""
        done = by_ex.get(ex["name"])
        done_str = ""
        if done:
            done_str = f"\n      → done so far: {', '.join(done)}"
        lines.append(
            f"    • {ex['name']} — {ex['sets']}×{ex['rep_range']}{rpe}{cardio}{prev_str}{done_str}"
        )

    started = active.started_at.strftime("%H:%M UTC")
    return (
        f"\n🔴 ACTIVE WORKOUT — BLAKE IS CURRENTLY IN A {active.session_type.upper()} SESSION "
        f"(started {started})\n"
        f"Every training question in this conversation refers to TODAY'S {active.session_type} "
        f"unless Blake EXPLICITLY says otherwise.\n"
        f"NEVER mix this with another session type's exercises or weights.\n\n"
        f"Today's {active.session_type} exercises (in order, with last session's logged sets "
        f"and what's already done this session):\n"
        + "\n".join(lines)
        + "\n"
    )


def build_context(user_id: int) -> str:
    """Build a concise data-rich context block to prepend to Ero conversations."""
    user = db.session.get(User, user_id)
    today = date.today()
    seven_days_ago = today - timedelta(days=14)
    active_block = _format_active_session(user_id)

    # weights
    weights = (WeightLog.query
               .filter(WeightLog.user_id == user_id)
               .order_by(WeightLog.logged_at.desc())
               .limit(10).all())
    weight_lines = [f"{w.logged_at.strftime('%Y-%m-%d')}: {w.weight_kg}kg" for w in weights]

    # recent sessions
    sessions = (WorkoutSession.query
                .filter(WorkoutSession.user_id == user_id,
                        WorkoutSession.completed_at != None,
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

    ctx = f"""[BLAKE'S LIVE DATA — {today} ({today.strftime('%A')}, scheduled session: {today_session})]
{active_block or ''}
GOALS & TARGETS:
{_format_targets(user)}

CURRENT PROGRAM (ULPPL — rest Wed & Sun):
{_format_program()}

CURRENT WORKING WEIGHTS (most recent logged sets per exercise — this IS his program loading):
{_format_working_weights(user_id)}

CURRENT MEAL PLAN (today's status — this IS his nutrition plan, not generic advice):
{_format_meal_plan(user_id, today)}

Today so far: {eaten_count}/{total_meals} meals eaten, {water_today}ml water (target {user.daily_water_target_ml}ml)

BODYWEIGHT TREND:
{_format_weight_trend(user_id)}

SCHEDULE ADHERENCE (last 14 days — ✓=trained, ✗=missed, 💤=rest, ?=said trained but no session logged):
{_format_schedule_adherence(user_id)}

STALLED LIFTS (top weight unchanged in last 2-3 sessions — flag if relevant):
{_format_stalls(user_id)}

RECENT TOP-WEIGHT HITS (last 14 days):
{_format_recent_prs(user_id)}

Raw recent bodyweight entries (most recent first):
{chr(10).join('  ' + w for w in weight_lines) if weight_lines else '  (none)'}

Recent completed workouts (last 14 days):
{chr(10).join('  ' + s for s in session_lines) if session_lines else '  (none yet)'}

Recent daily check-ins:
{chr(10).join('  ' + d for d in daily_lines) if daily_lines else '  (none)'}
{weekly_block}
[END OF LIVE DATA — everything above is the source of truth. Reference it. Never claim you don't have it.]
"""
    return ctx


def _current_session_lock_note(user_id: int) -> str | None:
    """One-line reminder injected into every user message when there's an active session.
    Forces Claude to anchor on the active session even if old assistant turns drifted."""
    active = (WorkoutSession.query
              .filter(WorkoutSession.user_id == user_id,
                      WorkoutSession.completed_at == None)
              .order_by(WorkoutSession.started_at.desc())
              .first())
    if not active:
        return None
    return (
        f"\n\n[SYSTEM REMINDER — not from Blake: he is currently IN an active "
        f"{active.session_type.upper()} session. Any training question refers to {active.session_type}. "
        f"If any earlier assistant reply in this thread referenced a different session, that reply was "
        f"wrong — silently correct course, do NOT re-assert the wrong session or ask him to confirm.]"
    )


_TOPIC_ANCHOR_NOTE = (
    "\n\n[SYSTEM REMINDER — not from Blake: your reply must be about the message Blake "
    "JUST sent above this reminder. Earlier turns in this thread are background only — "
    "they are NOT the topic. If Blake's last message named a venue (Subway, GYG, Maccas, "
    "KFC, Nando's, etc.), your reply talks about THAT venue and nothing else. If he named "
    "an exercise or session type, your reply is about THAT exercise/session. Before you "
    "type your answer, silently re-read his last message and check: is every venue, "
    "exercise, weight, and meal in your reply directly tied to that line? If not, rewrite. "
    "Do NOT paraphrase his earlier messages back at him as if they were his current "
    "question. Do NOT switch to a topic from earlier in the thread.]"
)


def chat_with_ero(user_id: int, history: list[dict], user_message: str) -> str:
    """Send a chat message and return Ero's reply (with tool-use)."""
    client = _client()
    if not client:
        return "(Ero is offline — ANTHROPIC_API_KEY not configured.)"

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    lock_note = _current_session_lock_note(user_id)
    final_user = user_message + _TOPIC_ANCHOR_NOTE + (lock_note or "")
    messages = list(history) + [{"role": "user", "content": final_user}]
    text, _calls = _run_tool_loop(user_id, system, messages)
    return text


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
        "Blake just submitted his weekly check-in. This is a major coaching moment — be thorough.\n\n"
        "STRUCTURE your response in these sections (use real headers, e.g. '## Last week'):\n\n"
        "1. **Last week's debrief** — Reference his EXACT weight change (week-over-week from the trend), "
        "specific lift wins or stalls (from the auto-detected stalls/PRs block), his actual nutrition "
        "adherence, his missed/completed sessions from the 14-day schedule. Quote his own answers back.\n\n"
        "2. **What's working / what's not** — call out 2-3 specific things he's doing well, and 1-2 "
        "things to fix. Specific. No vague praise.\n\n"
        "3. **Next week's plan** — like a daily brief but for the whole week. For EACH training day "
        "(Mon-Sat with rest Wed/Sun), tell him: which session, the ONE lift to push, the target weight "
        "to aim for based on his current working weights. Mention key nutrition focus for the week. "
        "Mention sleep / recovery priorities if his check-in flagged anything.\n\n"
        "4. **One commitment** — pick ONE specific outcome he should commit to (e.g. 'Hack Squat 132.5×8 "
        "by Saturday', or 'Hit Meal 4 every weekday'). Make him agree to it.\n\n"
        "Casual coach tone, 'man'/'bro'/'g' naturally. Reference actual numbers throughout. "
        "Tie back to his 70kg lean-bulk goal. If macro changes are needed, USE THE TOOLS to "
        "actually update meals/targets — don't just suggest.\n\n"
        f"His weekly check-in answers:\n{checkin_summary}"
    )

    messages = [{"role": "user", "content": prompt}]
    text, _calls = _run_tool_loop(user_id, system, messages, max_iters=8)
    return text


def proactive_check(user_id: int) -> str | None:
    """
    Called when Blake opens the app. Ero reviews the live data and decides whether
    to drop a proactive message. If nothing's worth saying, returns None.

    Throttled: at most one proactive nudge every 6 hours.
    """
    last_asst = (ChatMessage.query.filter_by(user_id=user_id, role="assistant")
                 .order_by(ChatMessage.created_at.desc()).first())
    if last_asst and (datetime.utcnow() - last_asst.created_at) < timedelta(hours=6):
        return None

    client = _client()
    if not client:
        return None

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    prompt = (
        "You're Blake's PT. He just opened the app. Review his live data above.\n\n"
        "Is there ANYTHING worth proactively flagging to him right now — something a real "
        "coach would text his client about unprompted? Examples:\n"
        "- A lift stalled at the same weight for 2+ sessions → suggest fix\n"
        "- A scheduled session he missed → reschedule it\n"
        "- Bodyweight stalled a full week → tell him to add food, suggest where\n"
        "- New top weight he hasn't been congratulated for → brief celebration\n"
        "- Pattern across daily check-ins (low sleep, low energy, low nutrition adherence) → address it\n"
        "- Today's planned session not yet started after 1pm on a training day → prompt him\n\n"
        "RULES:\n"
        "- Be SPECIFIC. Cite the exact lift, weight, date, or value from the data.\n"
        "- Be SHORT. 1–3 sentences max. This is a text from his coach, not an essay.\n"
        "- Be the COACH voice — direct, slightly pushy, warm. Use 'man'/'bro'/'g'.\n"
        "- One topic only. Don't cram multiple observations into one message.\n"
        "- If nothing significant — and 'nothing significant' is the right call most days — "
        "respond with exactly: SKIP\n"
        "- Do NOT send generic check-ins like 'how's it going?'. Only data-driven substance."
    )

    try:
        resp = client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"[ero] proactive_check failed: {e}", flush=True)
        return None

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    if not text or text.upper().startswith("SKIP") or len(text) < 25:
        return None

    msg = ChatMessage(user_id=user_id, role="assistant", content=text)
    db.session.add(msg)
    db.session.commit()
    return text


EROS_TOOLS = [
    {
        "name": "update_meal",
        "description": (
            "Update an existing meal in Blake's plan. Use this when he agrees to a meal change "
            "or you want to adjust macros to hit his daily targets. Only provide fields you "
            "want to change. ALWAYS recompute macros coherently — don't add isolated grams "
            "without a real food item to back them. Example: if adding 20g WPI to a shake, "
            "increment protein by 18, carbs by 1, fat by 0.5, calories by 80."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_id": {"type": "integer", "description": "The meal ID from the meal plan in context"},
                "name": {"type": "string", "description": "New full meal description with portions"},
                "scheduled_time": {"type": "string", "description": "HH:MM 24h, e.g. 13:15"},
                "calories": {"type": "integer"},
                "protein": {"type": "integer"},
                "carbs": {"type": "integer"},
                "fat": {"type": "integer"},
                "reasoning": {"type": "string", "description": "Brief reason for the change for the response message"},
            },
            "required": ["meal_id"],
        },
    },
    {
        "name": "add_meal",
        "description": "Add a new meal to Blake's daily plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "scheduled_time": {"type": "string"},
                "calories": {"type": "integer"},
                "protein": {"type": "integer"},
                "carbs": {"type": "integer"},
                "fat": {"type": "integer"},
                "reasoning": {"type": "string"},
            },
            "required": ["name", "calories", "protein", "carbs", "fat"],
        },
    },
    {
        "name": "delete_meal",
        "description": "Remove a meal from Blake's plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_id": {"type": "integer"},
                "reasoning": {"type": "string"},
            },
            "required": ["meal_id"],
        },
    },
    {
        "name": "update_targets",
        "description": (
            "Adjust Blake's daily nutrition targets. Use sparingly — typically only when his "
            "weight has stalled or accelerated for a full week. Don't tweak randomly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "daily_calorie_target": {"type": "integer"},
                "daily_protein_target": {"type": "integer"},
                "daily_carb_target": {"type": "integer"},
                "daily_fat_target": {"type": "integer"},
                "daily_water_target_ml": {"type": "integer"},
                "reasoning": {"type": "string"},
            },
        },
    },
    {
        "name": "log_weight",
        "description": "Log a new bodyweight entry for Blake (when he tells you his weight in chat).",
        "input_schema": {
            "type": "object",
            "properties": {
                "weight_kg": {"type": "number"},
            },
            "required": ["weight_kg"],
        },
    },
]


def _execute_tool(user_id: int, name: str, args: dict) -> dict:
    """Run a tool action and return a result dict for the tool_result message."""
    try:
        if name == "update_meal":
            m = Meal.query.filter_by(id=args["meal_id"], user_id=user_id, is_active=True).first()
            if not m:
                return {"error": f"Meal {args['meal_id']} not found"}
            for f in ("name", "scheduled_time"):
                if f in args and args[f] is not None:
                    setattr(m, f, args[f])
            for f in ("calories", "protein", "carbs", "fat"):
                if f in args and args[f] is not None:
                    setattr(m, f, int(args[f]))
            db.session.commit()
            return {
                "ok": True, "meal_id": m.id, "name": m.name,
                "calories": m.calories, "protein": m.protein, "carbs": m.carbs, "fat": m.fat,
            }
        elif name == "add_meal":
            max_order = db.session.query(func.max(Meal.sort_order)).filter_by(user_id=user_id).scalar() or 0
            m = Meal(
                user_id=user_id, name=args["name"],
                scheduled_time=args.get("scheduled_time", ""),
                calories=int(args.get("calories", 0)),
                protein=int(args.get("protein", 0)),
                carbs=int(args.get("carbs", 0)),
                fat=int(args.get("fat", 0)),
                sort_order=max_order + 1, is_active=True,
            )
            db.session.add(m)
            db.session.commit()
            return {"ok": True, "created_id": m.id, "name": m.name}
        elif name == "delete_meal":
            m = Meal.query.filter_by(id=args["meal_id"], user_id=user_id, is_active=True).first()
            if not m:
                return {"error": f"Meal {args['meal_id']} not found"}
            m.is_active = False
            db.session.commit()
            return {"ok": True, "deleted_id": m.id}
        elif name == "update_targets":
            u = db.session.get(User, user_id)
            for f in ("daily_calorie_target", "daily_protein_target", "daily_carb_target",
                      "daily_fat_target", "daily_water_target_ml"):
                if f in args and args[f] is not None:
                    setattr(u, f, int(args[f]))
            db.session.commit()
            return {"ok": True, "targets": {
                "kcal": u.daily_calorie_target, "p": u.daily_protein_target,
                "c": u.daily_carb_target, "f": u.daily_fat_target,
                "water_ml": u.daily_water_target_ml,
            }}
        elif name == "log_weight":
            w = WeightLog(user_id=user_id, weight_kg=float(args["weight_kg"]))
            db.session.add(w)
            db.session.commit()
            return {"ok": True, "weight_kg": w.weight_kg}
        return {"error": f"unknown tool {name}"}
    except Exception as e:
        return {"error": str(e)}


# Imports used by tool execution
from sqlalchemy import func


def _run_tool_loop(user_id: int, system: str, messages: list, max_iters: int = 6) -> tuple[str, list]:
    """Run the Claude tool-use loop. Returns (final_text, tool_calls_executed)."""
    client = _client()
    tool_calls_log = []
    for _ in range(max_iters):
        resp = client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system,
            tools=EROS_TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            return text, tool_calls_log

        # Append assistant turn including the tool_use blocks
        assistant_blocks = []
        tool_uses = []
        for b in resp.content:
            if b.type == "text":
                assistant_blocks.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                assistant_blocks.append({
                    "type": "tool_use", "id": b.id, "name": b.name, "input": b.input,
                })
                tool_uses.append(b)
        messages.append({"role": "assistant", "content": assistant_blocks})

        # Execute each tool, attach results
        result_blocks = []
        for tu in tool_uses:
            res = _execute_tool(user_id, tu.name, tu.input or {})
            tool_calls_log.append({"name": tu.name, "input": tu.input, "result": res})
            result_blocks.append({
                "type": "tool_result", "tool_use_id": tu.id,
                "content": json.dumps(res),
            })
        messages.append({"role": "user", "content": result_blocks})

    return "(Ero ran out of tool iterations — try again.)", tool_calls_log


def chat_with_ero_multimodal(user_id: int, history: list[dict], user_message: str,
                              image_url: str | None = None) -> str:
    """Chat with image support + tool use loop."""
    client = _client()
    if not client:
        return "(Ero is offline — ANTHROPIC_API_KEY not configured.)"

    context = build_context(user_id)
    system = ERO_SYSTEM_PROMPT + "\n\n" + context

    lock_note = _current_session_lock_note(user_id)
    user_content: list[dict] = []
    if image_url:
        user_content.append({
            "type": "image",
            "source": {"type": "url", "url": image_url},
        })
    user_content.append({
        "type": "text",
        "text": (user_message or "(image)") + _TOPIC_ANCHOR_NOTE + (lock_note or ""),
    })

    messages = list(history) + [{"role": "user", "content": user_content}]
    text, _calls = _run_tool_loop(user_id, system, messages)
    return text


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
