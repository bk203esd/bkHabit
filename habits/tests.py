from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from . import views


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
        self.assertTrue(self.user_model.objects.filter(
            username="newuser").exists())
        self.assertTrue(response.context["user"].is_authenticated)

    def test_logout_redirects_to_landing(self):
        self.client.login(username="tester", password=self.password)
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(response, reverse("landing"))
        self.assertFalse(response.context["user"].is_authenticated)


class TemplateAndRouteContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="route_tester",
            password="RoutePass123!",
        )

    def test_route_name_contract(self):
        self.assertEqual(reverse("landing"), "/")
        self.assertEqual(reverse("home"), "/home/")
        self.assertEqual(reverse("signup"), "/signup/")
        self.assertEqual(reverse("login"), "/accounts/login/")
        self.assertEqual(reverse("logout"), "/accounts/logout/")

    def test_views_resolution_contract(self):
        self.assertEqual(resolve("/").func, views.landing)
        self.assertEqual(resolve("/signup/").func, views.signup)

        resolved_home = resolve("/home/").func
        self.assertEqual(
            getattr(resolved_home, "__name__", ""),
            getattr(views.home, "__name__", ""),
        )

    def test_landing_uses_expected_template(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_signup_get_uses_expected_template(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_login_get_uses_expected_template(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_home_authenticated_uses_expected_template(self):
        self.client.login(username="route_tester", password="RoutePass123!")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
