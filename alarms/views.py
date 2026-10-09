from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import AlarmForm
from .models import Alarm, WEEKDAY_CHOICES


@login_required
def alarm_list(request):
    alarms = Alarm.objects.filter(user=request.user)
    weekday_labels = dict(WEEKDAY_CHOICES)
    enriched = []
    for alarm in alarms:
        enriched.append(
            {
                "alarm": alarm,
                "days": [weekday_labels[day] for day in alarm.weekday_list()],
            }
        )
    return render(request, "alarms/list.html", {"alarms": enriched})


@login_required
def alarm_create(request):
    if request.method == "POST":
        form = AlarmForm(request.POST)
        if form.is_valid():
            alarm = form.save(commit=False)
            alarm.user = request.user
            alarm.save()
            messages.success(request, "Alarm created.")
            return redirect("alarm_list")
    else:
        form = AlarmForm()
    return render(request, "alarms/form.html", {"form": form, "title": "New alarm"})


@login_required
def alarm_edit(request, pk):
    alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
    if request.method == "POST":
        form = AlarmForm(request.POST, instance=alarm)
        if form.is_valid():
            form.save()
            messages.success(request, "Alarm updated.")
            return redirect("alarm_list")
    else:
        form = AlarmForm(instance=alarm)
    return render(request, "alarms/form.html", {"form": form, "title": "Edit alarm", "alarm": alarm})


@login_required
@require_POST
def alarm_delete(request, pk):
    alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
    alarm.delete()
    messages.success(request, "Alarm deleted.")
    return redirect("alarm_list")


@login_required
@require_POST
def alarm_toggle(request, pk):
    alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
    alarm.enabled = not alarm.enabled
    alarm.save(update_fields=["enabled", "updated_at"])
    return redirect("alarm_list")


@login_required
@require_GET
def alarms_due(request):
    """Return alarms due in the current local minute for browser notifications."""
    now = timezone.localtime()
    due = []
    for alarm in Alarm.objects.filter(user=request.user, enabled=True):
        if alarm.is_due_now(now):
            due.append(
                {
                    "id": alarm.id,
                    "title": alarm.title,
                    "time": alarm.time.strftime("%H:%M"),
                    "mode": alarm.mode,
                }
            )
    return JsonResponse({"alarms": due, "server_time": now.isoformat()})


@login_required
@require_POST
def alarm_ack(request, pk):
    alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
    mode = alarm.mode
    title = alarm.title
    alarm.mark_triggered()
    return JsonResponse({"ok": True, "title": title, "mode": mode})
