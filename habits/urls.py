from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home/", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("habits/", views.habits_list, name="habits_list"),
    path("habits/new/", views.habit_create, name="habit_create"),
    path("habits/<int:pk>/edit/", views.habit_update, name="habit_update"),
    path("habits/<int:pk>/delete/", views.habit_delete, name="habit_delete"),
    path("habits/<int:pk>/checkin/", views.habit_toggle_checkin,
         name="habit_toggle_checkin"),
    path("habits/<int:pk>/history/", views.habit_history, name="habit_history"),
]
