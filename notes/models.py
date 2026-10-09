from django.conf import settings
from django.db import models


class Folder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="note_folders",
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="note_tags",
    )
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return self.name


class Note(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, help_text="Markdown supported")
    folder = models.ForeignKey(
        Folder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notes",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="notes")
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self) -> str:
        return self.title
