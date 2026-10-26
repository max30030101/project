"""Rule-based workout recommender.

It turns a person's goal, experience, equipment and weekly availability into a
structured plan, picking exercises from the Exercise table. It is deliberately
isolated behind `generate_plan()` so an LLM-backed generator can replace or
augment it later without touching views or templates.
"""
import random

from django.db import transaction

from shop.models import Product

from .models import Exercise, PlanDay, PlanExercise, WorkoutPlan

LEVEL_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}
EQUIP_RANK = {"none": 0, "home": 1, "gym": 2}

# goal -> (sets, reps, rest seconds, cardio finisher?)
SCHEMES = {
    "build_muscle": (4, "8-12", 75, False),
    "strength": (5, "4-6", 150, False),
    "lose_fat": (3, "12-15", 40, True),
    "endurance": (3, "15-20", 30, True),
    "general": (3, "10-12", 60, False),
}

FULL_BODY = [
    ("Full body A", ["legs", "chest", "back", "core"]),
    ("Full body B", ["legs", "shoulders", "back", "arms"]),
    ("Full body C", ["legs", "chest", "back", "core"]),
]
SPLITS = {
    2: FULL_BODY[:2],
    3: FULL_BODY,
    4: [("Upper body", ["chest", "back", "shoulders", "arms"]), ("Lower body & core", ["legs", "core"]),
        ("Upper body", ["back", "chest", "shoulders", "arms"]), ("Lower body & core", ["legs", "core"])],
    5: [("Push", ["chest", "shoulders", "arms"]), ("Pull", ["back", "arms"]), ("Legs & core", ["legs", "core"]),
        ("Upper body", ["chest", "back", "shoulders"]), ("Conditioning", ["cardio", "core", "legs"])],
    6: [("Push", ["chest", "shoulders", "arms"]), ("Pull", ["back", "arms"]), ("Legs & core", ["legs", "core"]),
        ("Push", ["shoulders", "chest", "arms"]), ("Pull", ["back", "arms"]), ("Legs & core", ["legs", "core"])],
}

GOAL_NOTES = {
    "build_muscle": "Aim to add a little weight or one rep each week. Eat enough protein and sleep 7–9 hours.",
    "strength": "Keep the first lift of each day heavy but clean. Rest fully between sets.",
    "lose_fat": "Short rests and a cardio finisher keep your heart rate up. Walk daily on non-training days.",
    "endurance": "Keep rests short and pace yourself. Add a few minutes to the cardio blocks as you improve.",
    "general": "Move well, stay consistent, and increase effort gradually.",
}

# goal -> shop category slugs worth suggesting
GEAR_CATEGORIES = {
    "build_muscle": ["strength-weights", "gym-accessories"],
    "strength": ["strength-weights", "gym-accessories"],
    "lose_fat": ["cardio-conditioning", "footwear-apparel"],
    "endurance": ["cardio-conditioning", "footwear-apparel"],
    "general": ["yoga-recovery", "gym-accessories"],
}


def _pick(pool, group, level, equip, n, rng, used):
    options = [e for e in pool if e.muscle_group == group and e.equipment_level <= equip
               and e.difficulty <= level and e.pk not in used]
    if not options:  # relax difficulty by one step rather than leaving a gap
        options = [e for e in pool if e.muscle_group == group and e.equipment_level <= equip
                   and e.difficulty <= level + 1 and e.pk not in used]
    rng.shuffle(options)
    options.sort(key=lambda e: e.equipment_level != equip)  # prefer kit the user actually has
    return options[:n]


@transaction.atomic
def generate_plan(user, goal, level, equipment, days_per_week, seed=None):
    rng = random.Random(seed)
    days_per_week = max(2, min(6, int(days_per_week)))
    sets, reps, rest, cardio_finisher = SCHEMES.get(goal, SCHEMES["general"])
    lvl, eq = LEVEL_RANK.get(level, 0), EQUIP_RANK.get(equipment, 0)
    pool = list(Exercise.objects.filter(is_active=True))

    goal_label = dict(WorkoutPlan._meta.get_field("goal").choices).get(goal, "Fitness")
    user.plans.filter(is_active=True).update(is_active=False)
    plan = WorkoutPlan.objects.create(
        user=user, title=f"{goal_label} — {days_per_week} days a week", goal=goal, level=level,
        equipment=equipment, days_per_week=days_per_week,
        summary=f"{GOAL_NOTES.get(goal, '')} Warm up for 5–10 minutes before each session and stop if anything hurts.",
    )
    for number, (title, groups) in enumerate(SPLITS[days_per_week], start=1):
        day = PlanDay.objects.create(plan=plan, day_number=number, title=title)
        groups = list(groups)
        if cardio_finisher and "cardio" not in groups:
            groups.append("cardio")
        used, order = set(), 0
        for group in groups:
            strength_groups = [g for g in groups if g not in ("cardio", "core")]
            n = 1 if group in ("cardio", "core") and len(groups) > 2 else max(1, min(3, 6 // max(len(strength_groups), 1)))
            for ex in _pick(pool, group, lvl, eq, n, rng, used):
                used.add(ex.pk)
                order += 1
                if group == "cardio":
                    PlanExercise.objects.create(day=day, exercise=ex, sets=1, reps="10–15 min", rest_seconds=0, order=order)
                elif group == "core":
                    PlanExercise.objects.create(day=day, exercise=ex, sets=3, reps="30–45 sec" if "Plank" in ex.name else "12-15", rest_seconds=45, order=order)
                else:
                    PlanExercise.objects.create(day=day, exercise=ex, sets=sets, reps=reps, rest_seconds=rest, order=order)
    return plan


def recommended_gear(goal, equipment, limit=4):
    slugs = list(GEAR_CATEGORIES.get(goal, GEAR_CATEGORIES["general"]))
    if equipment == "none" and "yoga-recovery" not in slugs:
        slugs.append("yoga-recovery")
    return (Product.objects.filter(is_active=True, stock__gt=0, category__slug__in=slugs)
            .select_related("category").order_by("-is_featured", "-created_at")[:limit])
