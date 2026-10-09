from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from alarms.models import Alarm
from events.models import Event
from notes.models import Note

from .forms import ApprovedAuthenticationForm, ProfileForm, RegisterForm
from .models import RegistrationStatus, UserProfile


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


@login_required
def dashboard(request):
    user = request.user
    context = {
        "upcoming_events": Event.objects.for_user(user).upcoming()[:5],
        "active_alarms": Alarm.objects.filter(user=user, enabled=True).order_by("time")[:5],
        "recent_notes": Note.objects.filter(user=user).order_by("-updated_at")[:5],
        "pinned_notes": Note.objects.filter(user=user, is_pinned=True).order_by("-updated_at")[:5],
    }
    return render(request, "dashboard.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registration submitted. An administrator must approve your account before you can sign in.",
            )
            return redirect("registration_pending")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


def registration_pending(request):
    return render(request, "registration/pending.html")


class DayFlowLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = ApprovedAuthenticationForm
    redirect_authenticated_user = True


@login_required
def profile_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Preferences saved.")
            return redirect("profile_settings")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/settings.html", {"form": form})


def superuser_required(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(superuser_required)
def registration_queue(request):
    pending = UserProfile.objects.filter(
        registration_status=RegistrationStatus.PENDING
    ).select_related("user")
    denied = UserProfile.objects.filter(
        registration_status=RegistrationStatus.DENIED
    ).select_related("user", "reviewed_by")[:50]
    approved = UserProfile.objects.filter(
        registration_status=RegistrationStatus.APPROVED
    ).select_related("user", "reviewed_by")[:50]
    return render(
        request,
        "admin_panel/registrations.html",
        {"pending": pending, "denied": denied, "approved": approved},
    )


@user_passes_test(superuser_required)
@require_POST
def approve_registration(request, profile_id):
    profile = get_object_or_404(UserProfile, pk=profile_id)
    profile.approve(request.user)
    messages.success(request, f"Approved {profile.user.username}.")
    return redirect("registration_queue")


@user_passes_test(superuser_required)
@require_POST
def deny_registration(request, profile_id):
    profile = get_object_or_404(UserProfile, pk=profile_id)
    profile.deny(request.user)
    messages.warning(request, f"Denied {profile.user.username}.")
    return redirect("registration_queue")
