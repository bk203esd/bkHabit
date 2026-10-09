from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "registration_status", "theme", "timezone", "created_at")
    list_filter = ("registration_status", "theme")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "reviewed_at")
