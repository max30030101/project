from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BodyMetricForm, RecommendForm, WorkoutLogForm
from .models import BodyMetric, WorkoutLog, WorkoutPlan
from .recommender import generate_plan, recommended_gear


def _streak(dates, today):
    """Consecutive days with a workout, ending today (or yesterday if today isn't logged yet)."""
    day = today if today in dates else today - timedelta(days=1)
    streak = 0
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


@login_required
def dashboard(request):
    user, today = request.user, date.today()
    logs = WorkoutLog.objects.filter(user=user)
    week_start = today - timedelta(days=today.weekday())
    week = logs.filter(date__gte=week_start)
    totals = week.aggregate(minutes=Sum("duration_minutes"), calories=Sum("calories_burned"))

    # last seven days of activity as simple bars
    by_day = {}
    for entry in logs.filter(date__gte=today - timedelta(days=6)):
        by_day[entry.date] = by_day.get(entry.date, 0) + entry.duration_minutes
    peak = max(by_day.values(), default=0) or 1
    activity = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        minutes = by_day.get(d, 0)
        activity.append({"label": d.strftime("%a"), "minutes": minutes, "pct": round(minutes / peak * 100), "today": d == today})

    plan = user.plans.filter(is_active=True).prefetch_related("days__items__exercise").first()
    next_day = None
    if plan:
        days = list(plan.days.all())
        last = logs.filter(plan_day__plan=plan).select_related("plan_day").first()
        if days:
            next_day = days[0] if not last else next((d for d in days if d.day_number == last.plan_day.day_number % len(days) + 1), days[0])

    weights = list(BodyMetric.objects.filter(user=user).order_by("-date")[:12])[::-1]
    weight_data = [{"date": w.date.strftime("%d %b"), "kg": float(w.weight_kg)} for w in weights]
    profile = user.profile
    return render(request, "workouts/dashboard.html", {
        "week_count": week.count(), "week_minutes": totals["minutes"] or 0, "week_calories": totals["calories"] or 0,
        "streak": _streak(set(logs.values_list("date", flat=True)), today),
        "total_workouts": logs.count(),
        "activity": activity, "recent": logs[:5], "plan": plan, "next_day": next_day,
        "weight_data": weight_data, "latest_weight": weights[-1].weight_kg if weights else profile.weight_kg,
        "weight_change": round(float(weights[-1].weight_kg - weights[0].weight_kg), 1) if len(weights) > 1 else None,
        "weight_form": BodyMetricForm(initial={"date": today}),
        "gear": recommended_gear(plan.goal if plan else profile.goal, plan.equipment if plan else profile.equipment),
    })


@login_required
def recommend(request):
    profile = request.user.profile
    initial = {"goal": profile.goal, "level": profile.experience, "equipment": profile.equipment, "days_per_week": profile.days_per_week}
    initial.update({k: v for k, v in request.GET.items() if k in initial})  # lets the home-page quick form prefill
    if request.method == "POST":
        form = RecommendForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            profile.goal, profile.experience, profile.equipment, profile.days_per_week = cd["goal"], cd["level"], cd["equipment"], cd["days_per_week"]
            profile.save()
            plan = generate_plan(request.user, cd["goal"], cd["level"], cd["equipment"], cd["days_per_week"])
            if not plan.days.filter(items__isnull=False).exists():
                messages.warning(request, "The exercise library is empty. Ask an admin to run: python manage.py seed_demo")
            else:
                messages.success(request, "Your personalised plan is ready.")
            return redirect("workouts:plan_detail", plan_id=plan.pk)
    else:
        form = RecommendForm(initial=initial)
    return render(request, "workouts/recommend.html", {"form": form})


@login_required
def plan_list(request):
    return render(request, "workouts/plan_list.html", {"plans": request.user.plans.all()})


@login_required
def plan_detail(request, plan_id):
    plan = get_object_or_404(WorkoutPlan.objects.prefetch_related("days__items__exercise"), pk=plan_id, user=request.user)
    return render(request, "workouts/plan_detail.html", {"plan": plan, "gear": recommended_gear(plan.goal, plan.equipment)})


@login_required
@require_POST
def plan_activate(request, plan_id):
    plan = get_object_or_404(WorkoutPlan, pk=plan_id, user=request.user)
    request.user.plans.update(is_active=False)
    plan.is_active = True
    plan.save(update_fields=["is_active"])
    messages.success(request, "That plan is now your active plan.")
    return redirect("workouts:plan_detail", plan_id=plan.pk)


@login_required
def log_workout(request):
    initial = {"date": date.today()}
    if request.GET.get("day"):
        initial["plan_day"] = request.GET["day"]
    form = WorkoutLogForm(request.POST or None, user=request.user, initial=initial)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.title = form.cleaned_data["title"]
        entry.save()
        messages.success(request, "Workout logged. Nice work.")
        return redirect("workouts:dashboard")
    return render(request, "workouts/log_form.html", {"form": form})


@login_required
def history(request):
    page = Paginator(WorkoutLog.objects.filter(user=request.user), 10).get_page(request.GET.get("page"))
    return render(request, "workouts/history.html", {
        "page_obj": page, "querystring": "",
        "weights": BodyMetric.objects.filter(user=request.user).order_by("-date")[:10],
    })


@login_required
@require_POST
def log_delete(request, log_id):
    get_object_or_404(WorkoutLog, pk=log_id, user=request.user).delete()
    messages.info(request, "Workout removed from your history.")
    return redirect("workouts:history")


@login_required
@require_POST
def add_weight(request):
    form = BodyMetricForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        BodyMetric.objects.update_or_create(user=request.user, date=cd["date"], defaults={"weight_kg": cd["weight_kg"]})
        request.user.profile.weight_kg = cd["weight_kg"]
        request.user.profile.save(update_fields=["weight_kg"])
        messages.success(request, "Weight saved.")
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("workouts:dashboard")
