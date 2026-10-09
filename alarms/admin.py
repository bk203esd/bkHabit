from django.contrib import admin

from .models import Alarm


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "time", "mode", "enabled")
    list_filter = ("mode", "enabled")
    search_fields = ("title", "user__username")
