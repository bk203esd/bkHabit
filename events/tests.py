from datetime import date, datetime, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import RegistrationStatus

from .models import Event, RecurrenceType


class EventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cal",
            password="complex-pass-123",
            is_active=True,
        )
        profile = self.user.profile
        profile.registration_status = RegistrationStatus.APPROVED
        profile.save()
        self.client.force_login(self.user)

    def test_weekly_occurrence(self):
        start = timezone.make_aware(datetime(2026, 10, 5, 9, 0))  # Monday
        event = Event.objects.create(
            user=self.user,
            title="Standup",
            start=start,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_weekdays="0,2",
        )
        self.assertTrue(event.occurs_on(date(2026, 10, 5)))
        self.assertTrue(event.occurs_on(date(2026, 10, 7)))
        self.assertFalse(event.occurs_on(date(2026, 10, 6)))

    def test_calendar_views_load(self):
        for view in ("month", "week", "day"):
            response = self.client.get(reverse("calendar"), {"view": view})
            self.assertEqual(response.status_code, 200)

    def test_create_event(self):
        response = self.client.post(
            reverse("event_create"),
            {
                "title": "Demo",
                "description": "",
                "start": "2026-10-09T10:00",
                "end": "2026-10-09T11:00",
                "all_day": False,
                "recurrence_type": RecurrenceType.NONE,
                "recurrence_until": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(user=self.user, title="Demo").exists())
