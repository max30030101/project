from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "goal", "experience", "equipment", "days_per_week", "is_premium")
    list_filter = ("goal", "experience", "equipment", "is_premium")
    search_fields = ("user__username", "user__email", "city")
