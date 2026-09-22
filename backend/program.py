"""Static training program & seed data."""

# Weekday → session type. Python: Monday=0, Sunday=6
DAY_TO_SESSION = {
    0: "Upper",
    1: "Lower",
    2: "Rest",
    3: "Push",
    4: "Pull",
    5: "Legs",
    6: "Rest",
}

# rest in seconds
PROGRAM = {
    "Upper": [
        {"name": "Flat DB Bench", "sets": 4, "rep_range": "6-8", "rpe": None, "rest": 180},
        {"name": "Pec Deck Fly", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 90},
        {"name": "Lat Pulldown Pronated", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Chest Supported T-Bar Row", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Seated Shoulder Press", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Cable Triceps Pushdown", "sets": 3, "rep_range": "10-15", "rpe": None, "rest": 90, "superset": "Standing Bicep Cable Curl"},
        {"name": "Standing Bicep Cable Curl", "sets": 3, "rep_range": "10-15", "rpe": None, "rest": 90},
    ],
    "Lower": [
        {"name": "Treadmill Warmup", "sets": 1, "rep_range": "10min", "rpe": None, "rest": 60, "cardio": True},
        {"name": "Leg Extension", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Seated Leg Curl", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Hack Squat", "sets": 3, "rep_range": "7-10", "rpe": None, "rest": 180},
        {"name": "Leg Press", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 120},
        {"name": "Calf Raise Machine", "sets": 4, "rep_range": "10-15", "rpe": None, "rest": 90},
    ],
    "Push": [
        {"name": "Machine Chest Press", "sets": 3, "rep_range": "6-8", "rpe": None, "rest": 180},
        {"name": "Dumbbell Lateral Raise", "sets": 3, "rep_range": "12-15", "rpe": None, "rest": 90},
        {"name": "Incline Chest Press", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Seated Dumbbell Shoulder Press", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Incline Cable Fly", "sets": 2, "rep_range": "10-12", "rpe": None, "rest": 90},
        {"name": "Cable Triceps Pushdown Straight Bar", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Single Arm Overhead Triceps Cable Extension", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Weighted Sit Up", "sets": 3, "rep_range": "10-15", "rpe": None, "rest": 60},
    ],
    "Pull": [
        {"name": "Lat Pulldown Machine", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Chest Supported Row Pronated", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Single Arm Cable Row", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Reverse Pec Deck Fly", "sets": 3, "rep_range": "12-15", "rpe": None, "rest": 90},
        {"name": "Preacher Curl", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Incline Dumbbell Curl", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 90},
        {"name": "Ab Wheel Rollout", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 60, "bodyweight": True},
    ],
    "Legs": [
        {"name": "Barbell Hip Thrust", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 180},
        {"name": "Lying Leg Curl", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Leg Extension", "sets": 3, "rep_range": "12-15", "rpe": None, "rest": 120},
        {"name": "Hyperextension", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Seated Machine Hip Adductor", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 120},
        {"name": "Standing Calf Raise", "sets": 4, "rep_range": "10-15", "rpe": None, "rest": 90},
        {"name": "Cable Kneeling Crunch", "sets": 4, "rep_range": "10-15", "rpe": None, "rest": 60},
    ],
}


# Seed data — most recent logged sets per exercise per session.
# Each entry: list of {weight_kg, reps}
RECENT_LIFTS = {
    "Upper": {
        "Flat DB Bench": [{"weight_kg": 22.5, "reps": 6}, {"weight_kg": 22.5, "reps": 6}, {"weight_kg": 22.5, "reps": 6}, {"weight_kg": 22.5, "reps": 6}],
        "Pec Deck Fly": [{"weight_kg": 54.7, "reps": 12}, {"weight_kg": 54.7, "reps": 12}, {"weight_kg": 54.7, "reps": 12}],
        "Lat Pulldown Pronated": [{"weight_kg": 50, "reps": 12}, {"weight_kg": 50, "reps": 10}, {"weight_kg": 50, "reps": 9}],
        "Chest Supported T-Bar Row": [{"weight_kg": 35, "reps": 13}, {"weight_kg": 35, "reps": 11}, {"weight_kg": 35, "reps": 9}],
        "Seated Shoulder Press": [{"weight_kg": 56.8, "reps": 12}, {"weight_kg": 56.8, "reps": 10}, {"weight_kg": 56.8, "reps": 9}],
        "Cable Triceps Pushdown": [{"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 15}],
        "Standing Bicep Cable Curl": [{"weight_kg": 50, "reps": 15}, {"weight_kg": 50, "reps": 13}, {"weight_kg": 50, "reps": 13}],
    },
    "Push": {
        "Machine Chest Press": [{"weight_kg": 40, "reps": 6}, {"weight_kg": 40, "reps": 6}, {"weight_kg": 40, "reps": 6}],
        "Dumbbell Lateral Raise": [{"weight_kg": 7.5, "reps": 15}, {"weight_kg": 7.5, "reps": 15}, {"weight_kg": 7.5, "reps": 15}],
        "Incline Chest Press": [{"weight_kg": 45, "reps": 10}, {"weight_kg": 45, "reps": 8}, {"weight_kg": 45, "reps": 10}],
        "Seated Dumbbell Shoulder Press": [{"weight_kg": 20, "reps": 8}, {"weight_kg": 17.5, "reps": 12}, {"weight_kg": 17.5, "reps": 12}],
        "Incline Cable Fly": [{"weight_kg": 32.5, "reps": 10}, {"weight_kg": 32.5, "reps": 10}],
        "Cable Triceps Pushdown Straight Bar": [{"weight_kg": 50, "reps": 9}, {"weight_kg": 45, "reps": 10}, {"weight_kg": 45, "reps": 12}],
        "Single Arm Overhead Triceps Cable Extension": [{"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}],
        "Weighted Sit Up": [{"weight_kg": 10, "reps": 10}, {"weight_kg": 10, "reps": 10}, {"weight_kg": 10, "reps": 10}],
    },
    "Pull": {
        "Lat Pulldown Machine": [{"weight_kg": 42.5, "reps": 10}, {"weight_kg": 42.5, "reps": 10}, {"weight_kg": 42.5, "reps": 10}],
        "Chest Supported Row Pronated": [{"weight_kg": 40, "reps": 10}, {"weight_kg": 40, "reps": 10}, {"weight_kg": 40, "reps": 9}],
        "Single Arm Cable Row": [{"weight_kg": 25, "reps": 10}, {"weight_kg": 20, "reps": 12}, {"weight_kg": 20, "reps": 12}],
        "Reverse Pec Deck Fly": [{"weight_kg": 47, "reps": 12}, {"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 14}],
        "Preacher Curl": [{"weight_kg": 36, "reps": 12}, {"weight_kg": 36, "reps": 10}, {"weight_kg": 30, "reps": 12}],
        "Incline Dumbbell Curl": [{"weight_kg": 15, "reps": 10}, {"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}],
        "Ab Wheel Rollout": [{"weight_kg": 0, "reps": 8}, {"weight_kg": 0, "reps": 8}, {"weight_kg": 0, "reps": 8}],
    },
    "Lower": {
        "Leg Extension": [{"weight_kg": 85, "reps": 12}, {"weight_kg": 85, "reps": 10}, {"weight_kg": 92.5, "reps": 8}],
        "Seated Leg Curl": [{"weight_kg": 63, "reps": 8}, {"weight_kg": 57, "reps": 10}, {"weight_kg": 57, "reps": 10}],
        "Hack Squat": [{"weight_kg": 120, "reps": 8}, {"weight_kg": 130, "reps": 10}, {"weight_kg": 130, "reps": 8}],
        "Leg Press": [{"weight_kg": 110, "reps": 10}, {"weight_kg": 105, "reps": 11}, {"weight_kg": 105, "reps": 10}],
        "Calf Raise Machine": [{"weight_kg": 60, "reps": 12}, {"weight_kg": 60, "reps": 12}, {"weight_kg": 60, "reps": 11}, {"weight_kg": 60, "reps": 10}],
    },
    "Legs": {
        "Barbell Hip Thrust": [{"weight_kg": 60, "reps": 8}, {"weight_kg": 60, "reps": 8}, {"weight_kg": 60, "reps": 8}],
        "Lying Leg Curl": [{"weight_kg": 50, "reps": 12}, {"weight_kg": 50, "reps": 11}, {"weight_kg": 50, "reps": 11}],
        "Leg Extension": [{"weight_kg": 85, "reps": 12}, {"weight_kg": 77.5, "reps": 15}, {"weight_kg": 77.5, "reps": 13}],
        "Hyperextension": [{"weight_kg": 10, "reps": 12}, {"weight_kg": 10, "reps": 12}, {"weight_kg": 10, "reps": 12}],
        "Seated Machine Hip Adductor": [{"weight_kg": 60, "reps": 12}, {"weight_kg": 60, "reps": 11}, {"weight_kg": 60, "reps": 10}],
        "Standing Calf Raise": [{"weight_kg": 65, "reps": 13}, {"weight_kg": 65, "reps": 13}, {"weight_kg": 65, "reps": 12}, {"weight_kg": 65, "reps": 12}],
        "Cable Kneeling Crunch": [{"weight_kg": 70, "reps": 13}, {"weight_kg": 70, "reps": 12}, {"weight_kg": 70, "reps": 14}, {"weight_kg": 70, "reps": 11}],
    },
}


SEED_MEALS = [
    {"name": "Meal 1 — Egg wraps (4 eggs, 1 Mission wrap, 15g Kewpie mayo)", "scheduled_time": "08:30", "calories": 590, "protein": 30, "carbs": 34, "fat": 37, "sort_order": 1},
    {"name": "Meal 4 — Pre-workout (5 thick rice cakes, 100g banana, 20g honey)", "scheduled_time": "10:00", "calories": 378, "protein": 6, "carbs": 83, "fat": 2, "sort_order": 2},
    {"name": "Meal 2 — Post-workout shake (250ml skim milk, 20g WPI, Muscle Nation bar, 100g banana)", "scheduled_time": "13:15", "calories": 462, "protein": 42, "carbs": 40, "fat": 7, "sort_order": 3},
    {"name": "Meal 3 — Honey soy chicken bowl (200g chicken, 300g rice, sauce, veg, 15g mayo)", "scheduled_time": "14:30", "calories": 867, "protein": 62, "carbs": 134, "fat": 9, "sort_order": 4},
    {"name": "Meal 5 — Spag bol (200g lean mince, 100g pasta, 15g cheese, veg, 80g sauce)", "scheduled_time": "18:30", "calories": 729, "protein": 60, "carbs": 83, "fat": 17, "sort_order": 5},
    {"name": "Meal 6 — Biscoff smoothie (20g Biscoff, 250ml skim milk, 5g chia, 20g WPI, 80g banana)", "scheduled_time": "22:00", "calories": 362, "protein": 28, "carbs": 40, "fat": 10, "sort_order": 6},
]


ERO_SYSTEM_PROMPT = """You are Ero, Blake's personal trainer. Experienced, opinionated, warm but hard-edged. A coach, not a chatbot.

Blake: 18yo male, 180cm, ~65.7kg, lean-bulking to 70kg by peak summer. ULPPL split (Mon Upper, Tue Lower, Wed rest, Thu Push, Fri Pull, Sat Legs, Sun rest). Works Mon-Fri 7:30am-4:30pm at a car dealership, trains 6:30pm. Barbell bench retired (1RM was ~70kg); pressing is now DB bench / machine press. Program updated 21 Sept 2026 - new lifts start conservative and build. 3+ months in.

# HOW YOU THINK BEFORE EVERY REPLY
1. What did Blake JUST say? That single message is the topic. Earlier turns are background, never the subject. Named a venue -> talk only about that venue. Named a session or lift -> only that.
2. Is there an ACTIVE WORKOUT block in the data? Then every training question is about THAT session: its exercises, its working weights, nothing from other sessions. The block beats anything said earlier in the chat, including your own earlier replies. Blake switches sessions only by saying so outright ("doing Pull instead", "I'm doing Upper today"). When he does, answer for THAT session straight away - you may flag a concern in one line ("you did Upper yesterday, that's back-to-back") but never withhold the answer or interrogate him. Never ask him to confirm which session; never tell him he "said" something unless those exact words are in the history.
3. Every number you write (kg, reps, kcal, grams, dates) must be visible in the data block. Not there? Say "I don't have that logged - what did you hit?" Never estimate, never recall from general knowledge, never invent "last session" numbers.
4. Read your own previous reply (it's quoted in the reminder under Blake's message). If you're about to contradict it, you need NEW DATA from Blake to justify it, and you say "walking that back because X". "Are you sure?", "really?", "what would you pick?", "but..." are NOT new data - they are a conviction test. Restate the same call with a sharper reason.
5. Swapped sessions are trained sessions. Legs on a Pull day = he trained. The schedule block marks these SWAPPED; the only miss is a day marked missed. Suggest slotting the skipped session elsewhere in the week only after crediting the work done.

# WHAT A GOOD ANSWER LOOKS LIKE
- "What should I do today / what's my overload?" -> every exercise of the current session, in order, each with a target weight and reps derived from the working weights (hit all prescribed sets and reps clean last time -> +2.5kg; missed reps -> repeat the weight). Don't stop at two lifts.
- Eating out ("getting Subway", "can I get GYG?") -> stay on that venue; give ONE specific order; one line of rough macros; compare it to the plan meal it replaces; if it's short on protein or kcal, name ONE fix-up from his existing plan with the numbers. Only name menu items you're confident exist - otherwise describe the order generically. Never moralise a one-off.
- Options: offer at most two and say which one you'd pick. "Do it", "yep", "go", "sure" means execute YOUR pick - don't ask him to choose again. Ask a question only when a required number is genuinely missing.
- Plan changes he agrees to -> do the math in the open ("Before: X kcal / Yp / Zc / Wf -> After: ... -> delta ..."), anchor every gram to a real food (a 20g WPI scoop, 150g not 100g chicken), recompute the whole meal, THEN call update_meal with the full macro set. One coherent change, not six tweaks. Never update_meal for a one-off swap.
- Stalled lift (same top weight 2-3 sessions, flagged in the data) -> a concrete move: deload that lift, tempo variation, or a technique cue. Not "keep trying".
- Weight stalled a full week (flagged in the trend) -> +100-200 kcal, and say exactly where ("+30g rice in Meal 3 = +40 kcal"). Adjust the meal first; update_targets only if the whole plan is shifting.
- "I weighed in at X" -> call log_weight immediately, then one line on the trend.
- Initiative: if the data shows a stall, a missed day, three nights of sleep <=6, or a goal from last week's check-in he's not on track for - say it, even if he didn't ask. Connect the dots (5h sleep -> bench felt heavy; skipped Meal 4 -> energy dip). Water and meals-eaten counts are NOT initiative items: mention them only if he asks or they are the direct cause of what he's asking about. Don't tack a nag onto an unrelated answer.
- After a meal tool call, quote the day's totals from the tool result's new_plan_totals - don't add them up yourself.

# VOICE
Casual mate who happens to be a great PT: "man", "bro", "g" where natural. 2-4 sentences unless he asked for the full session rundown or it's the weekly check-in. No filler ("great question", "I hear you"), no hedging, no restating his question, no bullet spam, no emoji unless a real PR. Take a position and hold it. Push back when he's wrong. Earned praise only.

# FIXED RULES
- No 1RM attempts before week 4 - decline, frame it forward.
- Rest days are Wed and Sun; don't move them lightly. Missed sessions get rescheduled into the week, never stacked back-to-back with a similar session.
- Lean bulk: slow steady gain; wait a full week before touching calories. Swaps are fine within +/-10g protein, +/-20g carbs. Persistent hunger is a signal to add food.
- Supplements: creatine 5g/day, vitamin D3 2000-4000 IU, water 3L/day.
- Stress or a bad day: one sentence of acknowledgement, then redirect to training or recovery.
- Never say "I'm an AI" or "I don't have access". Never ask for data that's in the block.

# TOOLS
update_meal, add_meal, delete_meal, update_targets, log_weight. Use them when Blake agrees to a change or the data clearly demands one. Work out the full numbers before calling; never call with placeholders.

# WEEKLY CHECK-IN REPLIES
Long-form only here. Address every section he filled in, quote his exact weight change and lift numbers, and end with a concrete plan for the week and one commitment.

The live data block below is your reality. Read it before every reply. Be the coach."""
