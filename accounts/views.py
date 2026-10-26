from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .emails import send_welcome_email
from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("workouts:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
        send_welcome_email(user)
        messages.success(request, f"Welcome to FitForge AI, {user.first_name}! A welcome email is on its way.")
        return redirect("workouts:recommend")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved. New plans will use these settings.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})
