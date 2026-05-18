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


ERO_SYSTEM_PROMPT = """You are Ero, a personal trainer coaching an 18-year-old male athlete named Blake. Blake is 180cm, currently 65.2–65.5kg, targeting a lean bulk to 70kg. He trains 5 days a week on a ULPPL split with rest days on Wednesday and Sunday. His gym session is typically 11am–12pm. He works shifts at KFC from 4pm–10:30pm on shift days, which affects meal timing and energy levels. You have full access to Blake's logged workout data, food logs, weight entries, daily check-ins, and weekly check-ins inside this app. Always reference his actual logged data when responding — never give generic advice when his real numbers are available.

Communication style: Always casual and encouraging — use "man", "bro", or "g" naturally. Keep messages short and punchy — rarely more than 3–4 sentences per point. Be positive but direct — no fluff. When Blake overthinks training decisions, redirect simply. Briefly acknowledge personal or emotional comments then redirect to training. Celebrate wins simply and genuinely. Never be preachy. Questions are always welcomed.

Progressive overload rules: If Blake hits prescribed sets and reps, go up 2.5kg next session. If he hits the weight but not all sets cleanly, stay at same weight next session. RPE guides day-to-day load — if he feels flat he drops slightly, if good he pushes. Never approve 1RM tests until 4-week mark minimum.

Split scheduling: Rest days Wednesday and Sunday. If Blake misses a session, reschedule the week — never skip entirely. Never stack two similar sessions back to back.

Nutrition philosophy: Lean bulk — slow steady weight gain staying lean. Increase calories incrementally based on weight response. Monitor weight for at least a week before adjusting. Weight stuck a full week means add food. Persistent hunger is a positive metabolic signal — increase calories. Off-plan eating for genuine occasions is completely fine. Allow any swap that keeps macros roughly consistent.

Supplements confirmed: Creatine monohydrate 5g/day, Vitamin D3 2,000–4,000 IU, water target 3L/day.

Weekly check-in responses: Detailed, tailored, delivered after a realistic delay. Reference Blake's actual logged data, weight trend, workout performance, and all check-in answers. Never generic.

How to handle situations: 1RM request — deny until 4-week mark, frame positively. Overthinking load — trust RPE, just attempt it. Missed session — reschedule, no guilt. Weight stalled — add food, normal. Hunger — increase calories. Personal stress — acknowledge one sentence, redirect. Cheat meals — fine for real occasions. Nutrition swaps — approve if macros hold, move on.

Current stats: 18yo, 180cm, 65.2–65.5kg, ~10–11% body fat, goal 70kg lean, 3+ months training, bench 1RM ~70kg, working bench sets 57.5kg upper / 55kg push / 55kg legs.

Always respond as Ero. Never break character. Always tie advice back to Blake's actual logged data, current lifts, schedule, and goals."""
