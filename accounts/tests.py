from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import RegistrationStatus, UserProfile


class AuthFlowTests(TestCase):
    def test_register_creates_pending_inactive_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "nova",
                "email": "nova@example.com",
                "password1": "complex-pass-123",
                "password2": "complex-pass-123",
                "timezone": "UTC",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="nova")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.registration_status, RegistrationStatus.PENDING)

    def test_pending_user_cannot_login(self):
        user = User.objects.create_user(username="wait", password="complex-pass-123", is_active=False)
        UserProfile.objects.filter(user=user).update(
            registration_status=RegistrationStatus.PENDING
        )
        response = self.client.post(
            reverse("login"),
            {"username": "wait", "password": "complex-pass-123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_denied_username_cannot_reregister(self):
        user = User.objects.create_user(
            username="blocked",
            email="blocked@example.com",
            password="complex-pass-123",
            is_active=False,
        )
        profile = user.profile
        profile.registration_status = RegistrationStatus.DENIED
        profile.save()

        response = self.client.post(
            reverse("register"),
            {
                "username": "blocked",
                "email": "other@example.com",
                "password1": "complex-pass-123",
                "password2": "complex-pass-123",
                "timezone": "UTC",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")

    def test_superuser_can_approve(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="complex-pass-123",
        )
        pending = User.objects.create_user(
            username="hope",
            email="hope@example.com",
            password="complex-pass-123",
            is_active=False,
        )
        profile = pending.profile
        profile.registration_status = RegistrationStatus.PENDING
        profile.save()

        self.client.force_login(admin)
        response = self.client.post(reverse("approve_registration", args=[profile.pk]))
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(pending.is_active)
        self.assertEqual(profile.registration_status, RegistrationStatus.APPROVED)
