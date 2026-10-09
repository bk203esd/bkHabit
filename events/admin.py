from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "start", "all_day", "recurrence_type")
    list_filter = ("all_day", "recurrence_type")
    search_fields = ("title", "user__username")
