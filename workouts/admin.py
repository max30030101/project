from django.contrib import admin

from .models import BodyMetric, Exercise, PlanDay, PlanExercise, WorkoutLog, WorkoutPlan


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "equipment_level", "difficulty", "is_active")
    list_filter = ("muscle_group", "equipment_level", "difficulty", "is_active")
    search_fields = ("name",)


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 0


class PlanDayInline(admin.StackedInline):
    model = PlanDay
    extra = 0
    show_change_link = True


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "goal", "level", "days_per_week", "is_active", "created_at")
    list_filter = ("goal", "level", "is_active")
    search_fields = ("title", "user__username")
    inlines = [PlanDayInline]


@admin.register(PlanDay)
class PlanDayAdmin(admin.ModelAdmin):
    list_display = ("plan", "day_number", "title")
    inlines = [PlanExerciseInline]


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "date", "duration_minutes", "calories_burned")
    list_filter = ("date",)
    search_fields = ("user__username", "title")


@admin.register(BodyMetric)
class BodyMetricAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "weight_kg")
    list_filter = ("date",)
