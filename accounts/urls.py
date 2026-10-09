from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    DayFlowLoginView,
    approve_registration,
    deny_registration,
    profile_settings,
    register,
    registration_pending,
    registration_queue,
)

urlpatterns = [
    path("login/", DayFlowLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("pending/", registration_pending, name="registration_pending"),
    path("settings/", profile_settings, name="profile_settings"),
    path("registrations/", registration_queue, name="registration_queue"),
    path("registrations/<int:profile_id>/approve/", approve_registration, name="approve_registration"),
    path("registrations/<int:profile_id>/deny/", deny_registration, name="deny_registration"),
]
