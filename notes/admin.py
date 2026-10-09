from django.contrib import admin

from .models import Folder, Note, Tag


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "folder", "is_pinned", "updated_at")
    list_filter = ("is_pinned",)
    search_fields = ("title", "user__username")
    filter_horizontal = ("tags",)
