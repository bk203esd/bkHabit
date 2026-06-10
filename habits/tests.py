from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.password = "TestPass123!"
        self.user = self.user_model.objects.create_user(
            username="tester",
            password=self.password,
        )

    def test_landing_is_public(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)

    def test_home_requires_authentication(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertIn("next=/home/", response.url)

    def test_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": "tester", "password": self.password},
            follow=True,
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.context["user"].is_authenticated)

    def test_signup_creates_user_and_auto_login(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(self.user_model.objects.filter(username="newuser").exists())
        self.assertTrue(response.context["user"].is_authenticated)

    def test_logout_redirects_to_landing(self):
        self.client.login(username="tester", password=self.password)
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(response, reverse("landing"))
        self.assertFalse(response.context["user"].is_authenticated)