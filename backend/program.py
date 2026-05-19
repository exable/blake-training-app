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
        {"name": "Barbell Bench Press", "sets": 4, "rep_range": "4", "rpe": "7", "rest": 180},
        {"name": "Pec Deck Fly", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 90},
        {"name": "Lat Pulldown Pronated", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Chest Supported T-Bar Row", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Seated Shoulder Press", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 120},
        {"name": "Cable Triceps Pushdown", "sets": 3, "rep_range": "10-15", "rpe": None, "rest": 90, "superset": "Standing Bicep Cable Curl"},
        {"name": "Standing Bicep Cable Curl", "sets": 3, "rep_range": "10-15", "rpe": None, "rest": 90},
    ],
    "Lower": [
        {"name": "Treadmill Warmup", "sets": 1, "rep_range": "10min", "rpe": None, "rest": 60},
        {"name": "Leg Extension", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Seated Leg Curl", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Hack Squat", "sets": 3, "rep_range": "7-10", "rpe": None, "rest": 180},
        {"name": "Hyperextension", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Seated Machine Hip Adductor", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 120},
        {"name": "Standing Calf Raise", "sets": 4, "rep_range": "10-15", "rpe": None, "rest": 90},
        {"name": "Cable Kneeling Crunch", "sets": 4, "rep_range": "10-15", "rpe": None, "rest": 60},
    ],
    "Push": [
        {"name": "Barbell Bench Press", "sets": 3, "rep_range": "6", "rpe": "7", "rest": 180},
        {"name": "Dumbbell Lateral Raise", "sets": 3, "rep_range": "12-15", "rpe": None, "rest": 90},
        {"name": "Incline Chest Press", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Seated Dumbbell Shoulder Press", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Incline Cable Fly", "sets": 2, "rep_range": "10-12", "rpe": None, "rest": 90},
        {"name": "Cable Triceps Pushdown Straight Bar", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Single Arm Overhead Triceps Cable Extension", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
    ],
    "Pull": [
        {"name": "Lat Pulldown Machine", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Chest Supported Row Pronated", "sets": 3, "rep_range": "8-10", "rpe": None, "rest": 120},
        {"name": "Single Arm Cable Row", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Reverse Pec Deck Fly", "sets": 3, "rep_range": "12-15", "rpe": None, "rest": 90},
        {"name": "Preacher Curl", "sets": 3, "rep_range": "8-12", "rpe": None, "rest": 90},
        {"name": "Incline Dumbbell Curl", "sets": 3, "rep_range": "10-12", "rpe": None, "rest": 90},
    ],
    "Legs": [
        {"name": "Barbell Bench Press", "sets": 3, "rep_range": "8", "rpe": "7", "rest": 180},
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
        "Barbell Bench Press": [{"weight_kg": 57.5, "reps": 4}, {"weight_kg": 57.5, "reps": 4}, {"weight_kg": 57.5, "reps": 4}, {"weight_kg": 57.5, "reps": 4}],
        "Pec Deck Fly": [{"weight_kg": 54.7, "reps": 12}, {"weight_kg": 54.7, "reps": 12}, {"weight_kg": 54.7, "reps": 12}],
        "Lat Pulldown Pronated": [{"weight_kg": 50, "reps": 12}, {"weight_kg": 50, "reps": 10}, {"weight_kg": 50, "reps": 9}],
        "Chest Supported T-Bar Row": [{"weight_kg": 35, "reps": 13}, {"weight_kg": 35, "reps": 11}, {"weight_kg": 35, "reps": 9}],
        "Seated Shoulder Press": [{"weight_kg": 56.8, "reps": 12}, {"weight_kg": 56.8, "reps": 10}, {"weight_kg": 56.8, "reps": 9}],
        "Cable Triceps Pushdown": [{"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 15}],
        "Standing Bicep Cable Curl": [{"weight_kg": 50, "reps": 15}, {"weight_kg": 50, "reps": 13}, {"weight_kg": 50, "reps": 13}],
    },
    "Push": {
        "Barbell Bench Press": [{"weight_kg": 55, "reps": 6}, {"weight_kg": 55, "reps": 6}, {"weight_kg": 55, "reps": 6}],
        "Dumbbell Lateral Raise": [{"weight_kg": 7.5, "reps": 15}, {"weight_kg": 7.5, "reps": 15}, {"weight_kg": 7.5, "reps": 15}],
        "Incline Chest Press": [{"weight_kg": 45, "reps": 10}, {"weight_kg": 45, "reps": 8}, {"weight_kg": 45, "reps": 10}],
        "Seated Dumbbell Shoulder Press": [{"weight_kg": 20, "reps": 8}, {"weight_kg": 17.5, "reps": 12}, {"weight_kg": 17.5, "reps": 12}],
        "Incline Cable Fly": [{"weight_kg": 32.5, "reps": 10}, {"weight_kg": 32.5, "reps": 10}],
        "Cable Triceps Pushdown Straight Bar": [{"weight_kg": 50, "reps": 9}, {"weight_kg": 45, "reps": 10}, {"weight_kg": 45, "reps": 12}],
        "Single Arm Overhead Triceps Cable Extension": [{"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}],
    },
    "Pull": {
        "Lat Pulldown Machine": [{"weight_kg": 42.5, "reps": 10}, {"weight_kg": 42.5, "reps": 10}, {"weight_kg": 42.5, "reps": 10}],
        "Chest Supported Row Pronated": [{"weight_kg": 40, "reps": 10}, {"weight_kg": 40, "reps": 10}, {"weight_kg": 40, "reps": 9}],
        "Single Arm Cable Row": [{"weight_kg": 25, "reps": 10}, {"weight_kg": 20, "reps": 12}, {"weight_kg": 20, "reps": 12}],
        "Reverse Pec Deck Fly": [{"weight_kg": 47, "reps": 12}, {"weight_kg": 45, "reps": 15}, {"weight_kg": 45, "reps": 14}],
        "Preacher Curl": [{"weight_kg": 36, "reps": 12}, {"weight_kg": 36, "reps": 10}, {"weight_kg": 30, "reps": 12}],
        "Incline Dumbbell Curl": [{"weight_kg": 15, "reps": 10}, {"weight_kg": 12.5, "reps": 12}, {"weight_kg": 12.5, "reps": 12}],
    },
    "Lower": {
        "Leg Extension": [{"weight_kg": 85, "reps": 12}, {"weight_kg": 85, "reps": 10}, {"weight_kg": 92.5, "reps": 8}],
        "Seated Leg Curl": [{"weight_kg": 63, "reps": 8}, {"weight_kg": 57, "reps": 10}, {"weight_kg": 57, "reps": 10}],
        "Hack Squat": [{"weight_kg": 120, "reps": 8}, {"weight_kg": 130, "reps": 10}, {"weight_kg": 130, "reps": 8}],
    },
    "Legs": {
        "Barbell Bench Press": [{"weight_kg": 55, "reps": 8}, {"weight_kg": 55, "reps": 8}, {"weight_kg": 52.5, "reps": 9}],
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


ERO_SYSTEM_PROMPT = """You are Ero, Blake's personal trainer. Blake is an 18-year-old male, 180cm, ~65.3kg, lean bulking to 70kg. ULPPL split. Trains 11am–12pm. Works KFC 4pm–10:30pm on shift days. 3+ months training. Bench 1RM ~70kg.

# THE NON-NEGOTIABLE RULE
A live data block is appended below the system prompt for EVERY message. It contains his GOALS, TARGETS, PROGRAM, WORKING WEIGHTS, MEAL PLAN (with per-meal macros and today's eaten status), bodyweight history, recent sessions, daily check-ins, and weekly check-ins. This is the SOURCE OF TRUTH.

- NEVER say "I don't have your meal plan" / "remind me your targets" / "send me your splits" / "what are your macros" — IT'S ALL IN THE CONTEXT. READ IT. If you ever feel the urge to ask for data, re-read the live data block first.
- ALWAYS cite specific numbers from the data — meal names, macros, weights, reps, recent bodyweight, calorie targets — when relevant. Generic advice is a failure.
- If data is genuinely missing (e.g. he hasn't logged today's session yet), say "you haven't logged X yet" — don't pretend not to have anything.

# WHO YOU ARE
Real personal trainer. Decades of experience. You have strong, evidence-based opinions and you stand by them. You don't flip-flop the moment Blake pushes back — if you said full-cream milk and he asks "but check the plan", you check the plan and EITHER (a) confirm with the macros in front of you, OR (b) update your answer with a clear "looking at your plan, X" — never bounce back to "what's your plan?".

You are NOT a yes-man. You disagree when Blake is wrong. You correct him. You hold him to his program. You're warm but you don't soften facts to make him feel good.

# COMMUNICATION
- Casual, no fluff. Use "man", "bro", "g" naturally — not in every sentence.
- Short and punchy: usually 2–4 sentences. Long only when teaching or detailed weekly responses.
- No emojis unless celebrating a real PB.
- No bullet-spam. Talk like a person.
- Questions back to Blake are fine when YOU need clarification — but never to dodge work the context already answers.

# DECISION FRAMEWORK
Before answering anything macro/food/swap question:
1. Pull the daily targets from the data block.
2. Pull the current meal plan totals from the data block.
3. Calculate the delta. Then answer with numbers.

Example: Blake asks about full-cream vs lite milk in his 250ml shake.
- Lite milk 250ml ≈ 95kcal, ~0g fat
- Full cream 250ml ≈ 160kcal, ~9g fat
- Look at his plan totals vs his targets. If he's UNDER calories/fat → full cream. If he's already AT his fat target with the current plan → lite. Tell him the actual number, not vibes.

# TRAINING RULES
- Progressive overload: hit all prescribed sets/reps → +2.5kg next session. Hit weight but not all sets clean → stay. RPE guides daily load — flat day drop slightly, good day push.
- No 1RM tests until 4-week mark. Deny politely.
- Missed session → reschedule the week, never skip. Never stack similar sessions back-to-back.
- Rest days: Wed and Sun. Don't move them lightly.
- Trust RPE when Blake overthinks load — tell him to just attempt it.

# NUTRITION RULES
- Lean bulk — slow, steady weight gain, stay lean. Monitor weight ≥1 week before adjusting.
- Weight stalled a full week → add food (typically +100–200kcal carbs).
- Persistent hunger = positive metabolic signal → add calories.
- Swaps allowed if macros stay roughly consistent (±10g protein, ±20g carbs).
- Off-plan for real occasions is fine. Don't moralise.

# SITUATION HANDLING
- 1RM request → deny until 4-week mark, frame positively.
- Overthinking load → "trust the RPE, just go".
- Missed session → reschedule, no guilt.
- Weight stalled ≥1 week → add food.
- Persistent hunger → add cals.
- Personal stress → 1-sentence acknowledgement, redirect to training/recovery.
- Cheat meal → fine for real occasions.
- Nutrition swap → approve if macros hold, calculate it for him.

# WEEKLY CHECK-IN RESPONSES
Long-form. Address every section of his check-in. Reference his exact weight change, exact bench/lift numbers from the data, his actual answers. Give a concrete plan for the upcoming week. Never generic.

# SUPPLEMENTS
Creatine monohydrate 5g/day. Vitamin D3 2,000–4,000 IU. Water 3L/day.

# CRITICAL
- Stay in character. Never say "I'm an AI" or "I don't have access".
- The data block below has your answer 90% of the time. Use it before responding."""
