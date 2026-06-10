from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from . import views
from .models import Habit, HabitCheckin


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
        self.assertEqual(reverse("habits_list"), "/habits/")
        self.assertEqual(reverse("habit_create"), "/habits/new/")

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


class HabitCrudTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.password = "HabitPass123!"
        self.user = self.user_model.objects.create_user(
            username="habit_owner",
            password=self.password,
        )
        self.other_user = self.user_model.objects.create_user(
            username="other_owner",
            password=self.password,
        )

    def login_main_user(self):
        self.client.login(username="habit_owner", password=self.password)

    def test_create_habit_assigns_current_user_as_owner(self):
        self.login_main_user()

        response = self.client.post(
            reverse("habit_create"),
            {
                "name": "Leer 20 minutos",
                "description": "Lectura nocturna",
                "frequency": Habit.Frequency.DAILY,
                "is_active": True,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("habits_list"))
        habit = Habit.objects.get(name="Leer 20 minutos")
        self.assertEqual(habit.owner, self.user)

    def test_list_shows_only_current_user_habits(self):
        Habit.objects.create(
            owner=self.user,
            name="Habito propio",
            frequency=Habit.Frequency.DAILY,
        )
        Habit.objects.create(
            owner=self.other_user,
            name="Habito ajeno",
            frequency=Habit.Frequency.WEEKLY,
        )

        self.login_main_user()
        response = self.client.get(reverse("habits_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Habito propio")
        self.assertNotContains(response, "Habito ajeno")

    def test_user_cannot_edit_other_user_habit(self):
        foreign_habit = Habit.objects.create(
            owner=self.other_user,
            name="Privado",
            frequency=Habit.Frequency.DAILY,
        )

        self.login_main_user()
        response = self.client.post(
            reverse("habit_update", args=[foreign_habit.pk]),
            {"name": "Hack", "description": "",
                "frequency": Habit.Frequency.DAILY, "is_active": True},
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_user_habit(self):
        foreign_habit = Habit.objects.create(
            owner=self.other_user,
            name="No borrar",
            frequency=Habit.Frequency.DAILY,
        )

        self.login_main_user()
        response = self.client.post(
            reverse("habit_delete", args=[foreign_habit.pk]))

        self.assertEqual(response.status_code, 404)

    def test_update_own_habit(self):
        own_habit = Habit.objects.create(
            owner=self.user,
            name="Original",
            frequency=Habit.Frequency.DAILY,
        )

        self.login_main_user()
        response = self.client.post(
            reverse("habit_update", args=[own_habit.pk]),
            {"name": "Actualizado", "description": "ok",
                "frequency": Habit.Frequency.WEEKLY, "is_active": True},
            follow=True,
        )

        self.assertRedirects(response, reverse("habits_list"))
        own_habit.refresh_from_db()
        self.assertEqual(own_habit.name, "Actualizado")
        self.assertEqual(own_habit.frequency, Habit.Frequency.WEEKLY)


class HabitTrackingTests(TestCase):
    def setUp(self):
        self.password = "TrackPass123!"
        self.user = get_user_model().objects.create_user(
            username="tracker",
            password=self.password,
        )
        self.other_user = get_user_model().objects.create_user(
            username="tracker_other",
            password=self.password,
        )

    def login_user(self):
        self.client.login(username="tracker", password=self.password)

    def test_daily_streak_current_and_max(self):
        habit = Habit.objects.create(
            owner=self.user,
            name="Diario",
            frequency=Habit.Frequency.DAILY,
        )
        today = timezone.localdate()

        habit.register_checkin(today - timedelta(days=6))
        habit.register_checkin(today - timedelta(days=5))
        habit.register_checkin(today - timedelta(days=4))
        habit.register_checkin(today - timedelta(days=1))
        habit.register_checkin(today)

        self.assertEqual(habit.streak_current(today), 2)
        self.assertEqual(habit.streak_max(), 3)

    def test_weekly_streak_current_and_max(self):
        habit = Habit.objects.create(
            owner=self.user,
            name="Semanal",
            frequency=Habit.Frequency.WEEKLY,
        )
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        habit.register_checkin(week_start)
        habit.register_checkin(week_start - timedelta(days=7))
        habit.register_checkin(week_start - timedelta(days=14))
        habit.register_checkin(week_start - timedelta(days=35))

        self.assertEqual(habit.streak_current(today), 3)
        self.assertEqual(habit.streak_max(), 3)

    def test_weekly_checkin_is_unique_per_week(self):
        habit = Habit.objects.create(
            owner=self.user,
            name="Semanal unico",
            frequency=Habit.Frequency.WEEKLY,
        )
        today = timezone.localdate()

        habit.register_checkin(today)
        habit.register_checkin(today + timedelta(days=2))

        self.assertEqual(HabitCheckin.objects.filter(habit=habit).count(), 1)

    def test_toggle_endpoint_marks_and_unmarks(self):
        habit = Habit.objects.create(
            owner=self.user,
            name="Toggle",
            frequency=Habit.Frequency.DAILY,
        )
        self.login_user()

        first = self.client.post(
            reverse("habit_toggle_checkin", args=[habit.pk]), follow=True)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(HabitCheckin.objects.filter(habit=habit).count(), 1)

        second = self.client.post(
            reverse("habit_toggle_checkin", args=[habit.pk]), follow=True)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(HabitCheckin.objects.filter(habit=habit).count(), 0)

    def test_user_cannot_toggle_other_user_habit(self):
        foreign_habit = Habit.objects.create(
            owner=self.other_user,
            name="Ajeno",
            frequency=Habit.Frequency.DAILY,
        )
        self.login_user()

        response = self.client.post(
            reverse("habit_toggle_checkin", args=[foreign_habit.pk]))
        self.assertEqual(response.status_code, 404)
