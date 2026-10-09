from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class AlarmMode(models.TextChoices):
    ONCE = "once", "One-time"
    WEEKLY = "weekly", "Weekly"


WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class Alarm(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alarms",
    )
    title = models.CharField(max_length=200)
    time = models.TimeField()
    mode = models.CharField(max_length=20, choices=AlarmMode.choices, default=AlarmMode.ONCE)
    once_date = models.DateField(null=True, blank=True)
    # Comma-separated weekday integers 0=Mon .. 6=Sun
    weekdays = models.CharField(max_length=32, blank=True)
    enabled = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["time", "title"]

    def __str__(self) -> str:
        return self.title

    def weekday_list(self) -> list[int]:
        if not self.weekdays:
            return []
        return [int(part) for part in self.weekdays.split(",") if part != ""]

    def set_weekdays(self, days: list[int]) -> None:
        self.weekdays = ",".join(str(day) for day in sorted(set(days)))

    def is_due_now(self, now=None) -> bool:
        now = now or timezone.localtime()
        if not self.enabled:
            return False

        # Already triggered in this minute
        if self.last_triggered_at:
            last = timezone.localtime(self.last_triggered_at)
            if last.year == now.year and last.month == now.month and last.day == now.day:
                if last.hour == now.hour and last.minute == now.minute:
                    return False

        if self.time.hour != now.hour or self.time.minute != now.minute:
            return False

        if self.mode == AlarmMode.ONCE:
            if not self.once_date:
                return False
            return self.once_date == now.date()

        if self.mode == AlarmMode.WEEKLY:
            return now.weekday() in self.weekday_list()

        return False

    def mark_triggered(self, now=None) -> None:
        now = now or timezone.now()
        self.last_triggered_at = now
        if self.mode == AlarmMode.ONCE:
            self.delete()
        else:
            self.save(update_fields=["last_triggered_at", "updated_at"])
