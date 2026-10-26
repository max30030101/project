from datetime import date

from django import forms

from accounts.choices import EQUIPMENT, GOALS, LEVELS

from .models import BodyMetric, PlanDay, WorkoutLog


class RecommendForm(forms.Form):
    goal = forms.ChoiceField(choices=GOALS, label="Main goal")
    level = forms.ChoiceField(choices=LEVELS, label="Experience level")
    equipment = forms.ChoiceField(choices=EQUIPMENT, label="Equipment you can use")
    days_per_week = forms.TypedChoiceField(choices=[(i, f"{i} days") for i in range(2, 7)], coerce=int, label="Days per week")


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


class WorkoutLogForm(forms.ModelForm):
    class Meta:
        model = WorkoutLog
        fields = ["plan_day", "title", "date", "duration_minutes", "calories_burned", "notes"]
        widgets = {"date": DateInput(), "notes": forms.Textarea(attrs={"rows": 3})}
        labels = {"plan_day": "Workout from your plan", "duration_minutes": "Duration (minutes)", "calories_burned": "Calories burned (optional)"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan_day"].queryset = PlanDay.objects.filter(plan__user=user, plan__is_active=True)
        self.fields["plan_day"].required = False
        self.fields["title"].required = False
        self.fields["title"].help_text = "Leave blank to use the plan day's name."

    def clean_date(self):
        d = self.cleaned_data["date"]
        if d > date.today():
            raise forms.ValidationError("Log workouts you have already done — pick today or an earlier date.")
        return d

    def clean(self):
        data = super().clean()
        if not data.get("title"):
            if data.get("plan_day"):
                data["title"] = data["plan_day"].title
            else:
                self.add_error("title", "Name your workout or pick one from your plan.")
        return data


class BodyMetricForm(forms.ModelForm):
    class Meta:
        model = BodyMetric
        fields = ["date", "weight_kg"]
        widgets = {"date": DateInput()}
        labels = {"weight_kg": "Weight (kg)"}

    def clean_date(self):
        d = self.cleaned_data["date"]
        if d > date.today():
            raise forms.ValidationError("The date can't be in the future.")
        return d
