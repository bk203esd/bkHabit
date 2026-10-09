from datetime import timedelta, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import RegistrationStatus

from .models import Alarm, AlarmMode


class AlarmTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ring",
            password="complex-pass-123",
            is_active=True,
        )
        profile = self.user.profile
        profile.registration_status = RegistrationStatus.APPROVED
        profile.save()
        self.client.force_login(self.user)

    def test_once_alarm_due_and_ack_deletes(self):
        now = timezone.localtime()
        alarm = Alarm.objects.create(
            user=self.user,
            title="Tea",
            time=now.time().replace(second=0, microsecond=0),
            mode=AlarmMode.ONCE,
            once_date=now.date(),
        )
        self.assertTrue(alarm.is_due_now(now))
        response = self.client.post(reverse("alarm_ack", args=[alarm.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Alarm.objects.filter(pk=alarm.pk).exists())

    def test_weekly_alarm_respects_weekdays(self):
        now = timezone.localtime()
        alarm = Alarm.objects.create(
            user=self.user,
            title="Stretch",
            time=time(8, 0),
            mode=AlarmMode.WEEKLY,
            weekdays=str(now.weekday()),
        )
        due_now = now.replace(hour=8, minute=0, second=0, microsecond=0)
        self.assertTrue(alarm.is_due_now(due_now))
        other = due_now + timedelta(days=1)
        # Rebuild a datetime on a different weekday at same clock time
        other = other.replace(hour=8, minute=0)
        if other.weekday() != now.weekday():
            self.assertFalse(alarm.is_due_now(other))
