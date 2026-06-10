from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    class Frequency(models.TextChoices):
        DAILY = "daily", "Diario"
        WEEKLY = "weekly", "Semanal"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    frequency = models.CharField(
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def _step_days(self):
        return 7 if self.frequency == self.Frequency.WEEKLY else 1

    def period_start_for(self, target_date):
        if self.frequency == self.Frequency.WEEKLY:
            return target_date - timedelta(days=target_date.weekday())
        return target_date

    def checked_in_period(self, target_date=None):
        target_date = target_date or timezone.localdate()
        period_start = self.period_start_for(target_date)
        return self.checkins.filter(period_start=period_start).exists()

    def register_checkin(self, target_date=None):
        target_date = target_date or timezone.localdate()
        period_start = self.period_start_for(target_date)
        return HabitCheckin.objects.get_or_create(
            habit=self,
            period_start=period_start,
        )

    def unregister_checkin(self, target_date=None):
        target_date = target_date or timezone.localdate()
        period_start = self.period_start_for(target_date)
        self.checkins.filter(period_start=period_start).delete()

    def streak_current(self, target_date=None):
        target_date = target_date or timezone.localdate()
        current_period = self.period_start_for(target_date)
        periods = set(self.checkins.values_list("period_start", flat=True))

        if current_period not in periods:
            return 0

        step = timedelta(days=self._step_days())
        streak = 0
        cursor = current_period

        while cursor in periods:
            streak += 1
            cursor -= step

        return streak

    def streak_max(self):
        periods = sorted(
            set(self.checkins.values_list("period_start", flat=True)))
        if not periods:
            return 0

        step = timedelta(days=self._step_days())
        max_streak = 1
        current_streak = 1

        for i in range(1, len(periods)):
            if periods[i] - periods[i - 1] == step:
                current_streak += 1
            else:
                current_streak = 1

            if current_streak > max_streak:
                max_streak = current_streak

        return max_streak


class HabitCheckin(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="checkins",
    )
    period_start = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["habit", "period_start"],
                name="unique_habit_period_checkin",
            )
        ]

    def __str__(self):
        return f"{self.habit.name} @ {self.period_start}"
