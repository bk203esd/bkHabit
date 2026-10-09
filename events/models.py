from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class RecurrenceType(models.TextChoices):
    NONE = "none", "Does not repeat"
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"


WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class EventQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def upcoming(self):
        now = timezone.now()
        return self.filter(
            Q(recurrence_type=RecurrenceType.NONE, start__gte=now)
            | ~Q(recurrence_type=RecurrenceType.NONE)
        ).order_by("start")


class Event(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    recurrence_type = models.CharField(
        max_length=20,
        choices=RecurrenceType.choices,
        default=RecurrenceType.NONE,
    )
    # Comma-separated weekday integers 0=Mon .. 6=Sun
    recurrence_weekdays = models.CharField(max_length=32, blank=True)
    recurrence_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["start"]

    def __str__(self) -> str:
        return self.title

    def weekday_list(self) -> list[int]:
        if not self.recurrence_weekdays:
            return []
        return [int(part) for part in self.recurrence_weekdays.split(",") if part != ""]

    def set_weekdays(self, weekdays: list[int]) -> None:
        self.recurrence_weekdays = ",".join(str(day) for day in sorted(set(weekdays)))

    def occurs_on(self, day) -> bool:
        """Return True if this event has an occurrence on the given date."""
        local_start = timezone.localtime(self.start).date()
        if day < local_start:
            return False
        if self.recurrence_until and day > self.recurrence_until:
            return False

        if self.recurrence_type == RecurrenceType.NONE:
            return day == local_start

        if self.recurrence_type == RecurrenceType.DAILY:
            return True

        if self.recurrence_type == RecurrenceType.WEEKLY:
            weekdays = self.weekday_list()
            if not weekdays:
                weekdays = [local_start.weekday()]
            return day.weekday() in weekdays

        if self.recurrence_type == RecurrenceType.MONTHLY:
            return day.day == local_start.day

        return False

    def occurrence_bounds(self, day):
        """Return (start, end) datetimes for an occurrence on day."""
        local_start = timezone.localtime(self.start)
        start_t = local_start.timetz() if not self.all_day else time(0, 0)
        start_dt = timezone.make_aware(datetime.combine(day, start_t.replace(tzinfo=None)))

        if self.end:
            local_end = timezone.localtime(self.end)
            duration = local_end - local_start
            end_dt = start_dt + duration
        elif self.all_day:
            end_dt = start_dt + timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(hours=1)
        return start_dt, end_dt
