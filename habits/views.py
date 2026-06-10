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
