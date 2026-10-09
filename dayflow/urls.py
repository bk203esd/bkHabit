from django.contrib import admin
from django.urls import include, path

from accounts.views import dashboard, landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="landing"),
    path("dashboard/", dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("alarms/", include("alarms.urls")),
    path("notes/", include("notes.urls")),
]
