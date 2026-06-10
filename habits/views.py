import calendar
from datetime import date, timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import HabitForm
from .models import Habit


def landing(request):
    return render(request, "landing.html")


@login_required
def home(request):
    habits = Habit.objects.filter(owner=request.user, is_active=True)
    today = timezone.localdate()

    habits_count = Habit.objects.filter(owner=request.user).count()
    active_count = habits.count()
    completed_count = sum(
        1 for habit in habits if habit.checked_in_period(today))
    best_current_streak = max([habit.streak_current(today)
                              for habit in habits], default=0)

    context = {
        "habits_count": habits_count,
        "active_count": active_count,
        "completed_count": completed_count,
        "best_current_streak": best_current_streak,
    }
    return render(request, "home.html", context)


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def habits_list(request):
    habits = Habit.objects.filter(owner=request.user)
    today = timezone.localdate()

    for habit in habits:
        habit.is_checked = habit.checked_in_period(today)
        habit.current_streak = habit.streak_current(today)
        habit.max_streak = habit.streak_max()
        habit.period_label = "hoy" if habit.frequency == Habit.Frequency.DAILY else "esta semana"

    return render(request, "habits/list.html", {"habits": habits})


@login_required
def habit_create(request):
    if request.method == "POST":
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.owner = request.user
            habit.save()
            return redirect("habits_list")
    else:
        form = HabitForm()

    return render(
        request,
        "habits/form.html",
        {"form": form, "page_title": "Crear habito", "submit_label": "Guardar"},
    )


@login_required
def habit_update(request, pk):
    habit = get_object_or_404(Habit, pk=pk, owner=request.user)

    if request.method == "POST":
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect("habits_list")
    else:
        form = HabitForm(instance=habit)

    return render(
        request,
        "habits/form.html",
        {"form": form, "page_title": "Editar habito", "submit_label": "Actualizar"},
    )


@login_required
def habit_delete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, owner=request.user)

    if request.method == "POST":
        habit.delete()
        return redirect("habits_list")

    return render(request, "habits/confirm_delete.html", {"habit": habit})


@require_POST
@login_required
def habit_toggle_checkin(request, pk):
    habit = get_object_or_404(Habit, pk=pk, owner=request.user, is_active=True)
    today = timezone.localdate()

    if habit.checked_in_period(today):
        habit.unregister_checkin(today)
    else:
        habit.register_checkin(today)

    return redirect("habits_list")


@login_required
def habit_history(request, pk):
    habit = get_object_or_404(Habit, pk=pk, owner=request.user)

    today = timezone.localdate()
    year_raw = request.GET.get("year")
    month_raw = request.GET.get("month")

    try:
        year = int(year_raw) if year_raw is not None else today.year
        month = int(month_raw) if month_raw is not None else today.month
        if month < 1 or month > 12:
            raise ValueError("month out of range")
        if year < 2000 or year > 2100:
            raise ValueError("year out of range")
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    cal = calendar.Calendar(firstweekday=0)
    month_matrix = cal.monthdatescalendar(year, month)

    first_day = date(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = date(year, month, last_day_num)

    checkins = habit.checkins.filter(
        period_start__gte=first_day, period_start__lte=last_day)
    completed_period_starts = set(
        checkins.values_list("period_start", flat=True))

    weeks = []
    for week in month_matrix:
        row = []
        for day_obj in week:
            is_outside = day_obj.month != month
            is_today = day_obj == today

            if habit.frequency == Habit.Frequency.DAILY:
                is_completed = day_obj in completed_period_starts
            else:
                monday_of_week = day_obj - timedelta(days=day_obj.weekday())
                is_completed = (day_obj.weekday() == 0) and (
                    monday_of_week in completed_period_starts)

            row.append(
                {
                    "day_number": day_obj.day,
                    "date_obj": day_obj,
                    "is_outside": is_outside,
                    "is_today": is_today,
                    "is_completed": is_completed,
                }
            )
        weeks.append(row)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    month_options = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    year_options = list(range(today.year - 2, today.year + 3))

    context = {
        "habit": habit,
        "weeks": weeks,
        "current_year": year,
        "current_month": month,
        "month_name": dict(month_options)[month],
        "month_options": month_options,
        "year_options": year_options,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "today_year": today.year,
        "today_month": today.month,
        "current_streak": habit.streak_current(today),
        "max_streak": habit.streak_max(),
    }
    return render(request, "habits/history.html", context)
