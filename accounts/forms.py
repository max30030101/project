from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=60, label="First name")
    email = forms.EmailField(label="Email address")

    class Meta:
        model = User
        fields = ("first_name", "username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Try signing in instead.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or email", widget=forms.TextInput(attrs={"autofocus": True}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "city", "age", "height_cm", "weight_kg", "goal", "experience", "equipment", "days_per_week"]
        labels = {
            "height_cm": "Height (cm)",
            "weight_kg": "Weight (kg)",
            "experience": "Experience level",
            "days_per_week": "Workout days per week",
        }
