from django.urls import path

from . import views

app_name = "workouts"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("recommend/", views.recommend, name="recommend"),
    path("plans/", views.plan_list, name="plans"),
    path("plans/<int:plan_id>/", views.plan_detail, name="plan_detail"),
    path("plans/<int:plan_id>/activate/", views.plan_activate, name="plan_activate"),
    path("log/new/", views.log_workout, name="log_workout"),
    path("log/<int:log_id>/delete/", views.log_delete, name="log_delete"),
    path("history/", views.history, name="history"),
    path("progress/weight/", views.add_weight, name="add_weight"),
]
