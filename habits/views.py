from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HabitForm
from .models import Habit


def landing(request):
    return render(request, "landing.html")


@login_required
def home(request):
    habits_count = Habit.objects.filter(owner=request.user).count()
    return render(request, "home.html", {"habits_count": habits_count})


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
