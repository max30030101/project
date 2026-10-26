from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from accounts.choices import EQUIPMENT, GOALS, LEVELS


class Exercise(models.Model):
    MUSCLES = [
        ("chest", "Chest"), ("back", "Back"), ("legs", "Legs"), ("shoulders", "Shoulders"),
        ("arms", "Arms"), ("core", "Core"), ("cardio", "Cardio"),
    ]
    EQUIPMENT_LEVELS = [(0, "Bodyweight"), (1, "Home (dumbbells, bands)"), (2, "Full gym")]
    DIFFICULTY = [(0, "Beginner"), (1, "Intermediate"), (2, "Advanced")]

    name = models.CharField(max_length=120, unique=True)
    muscle_group = models.CharField(max_length=12, choices=MUSCLES)
    equipment_level = models.PositiveSmallIntegerField(choices=EQUIPMENT_LEVELS, default=0)
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY, default=0)
    description = models.TextField(blank=True, help_text="Short how-to cue shown in plans.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["muscle_group", "name"]

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plans")
    title = models.CharField(max_length=120)
    goal = models.CharField(max_length=20, choices=GOALS)
    level = models.CharField(max_length=20, choices=LEVELS)
    equipment = models.CharField(max_length=10, choices=EQUIPMENT)
    days_per_week = models.PositiveSmallIntegerField()
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user})"


class PlanDay(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=80)

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


class PlanExercise(models.Model):
    day = models.ForeignKey(PlanDay, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    sets = models.PositiveSmallIntegerField()
    reps = models.CharField(max_length=20)
    rest_seconds = models.PositiveSmallIntegerField(default=60)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.exercise} {self.sets}×{self.reps}"


class WorkoutLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workout_logs")
    plan_day = models.ForeignKey(PlanDay, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs")
    title = models.CharField(max_length=120)
    date = models.DateField(default=date.today)
    duration_minutes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(600)])
    calories_burned = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(5000)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} on {self.date}"


class BodyMetric(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="body_metrics")
    date = models.DateField(default=date.today)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, validators=[MinValueValidator(20), MaxValueValidator(400)])

    class Meta:
        ordering = ["date"]
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user}: {self.weight_kg} kg on {self.date}"
