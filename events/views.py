from calendar import Calendar
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EventForm
from .models import Event


def _parse_anchor(request) -> date:
    raw = request.GET.get("date")
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return timezone.localdate()


def _events_for_day(events, day):
    return [event for event in events if event.occurs_on(day)]


@login_required
def calendar_view(request):
    view = request.GET.get("view", "month")
    if view not in {"month", "week", "day"}:
        view = "month"

    anchor = _parse_anchor(request)
    events = list(Event.objects.for_user(request.user))

    context = {
        "view_mode": view,
        "anchor": anchor,
    }

    if view == "month":
        cal = Calendar(firstweekday=0)
        weeks = []
        for week in cal.monthdatescalendar(anchor.year, anchor.month):
            weeks.append(
                [
                    {
                        "date": day,
                        "in_month": day.month == anchor.month,
                        "events": _events_for_day(events, day),
                    }
                    for day in week
                ]
            )
        first = anchor.replace(day=1)
        prev_month = (first - timedelta(days=1)).replace(day=1)
        next_month = (first.replace(day=28) + timedelta(days=10)).replace(day=1)
        context.update(
            {
                "weeks": weeks,
                "prev_date": prev_month,
                "next_date": next_month,
            }
        )
    elif view == "week":
        start = anchor - timedelta(days=anchor.weekday())
        days = [
            {
                "date": start + timedelta(days=i),
                "events": _events_for_day(events, start + timedelta(days=i)),
            }
            for i in range(7)
        ]
        context.update(
            {
                "days": days,
                "prev_date": start - timedelta(days=7),
                "next_date": start + timedelta(days=7),
            }
        )
    else:
        occurrences = []
        for event in _events_for_day(events, anchor):
            start_dt, end_dt = event.occurrence_bounds(anchor)
            occurrences.append({"event": event, "start": start_dt, "end": end_dt})
        occurrences.sort(key=lambda item: item["start"])
        context.update(
            {
                "day_events": occurrences,
                "prev_date": anchor - timedelta(days=1),
                "next_date": anchor + timedelta(days=1),
            }
        )

    return render(request, "events/calendar.html", context)


@login_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            messages.success(request, "Event created.")
            return redirect("calendar")
    else:
        initial = {}
        raw = request.GET.get("date")
        if raw:
            try:
                day = date.fromisoformat(raw)
                initial["start"] = datetime.combine(day, datetime.min.time().replace(hour=9))
                initial["end"] = datetime.combine(day, datetime.min.time().replace(hour=10))
            except ValueError:
                pass
        form = EventForm(initial=initial)
    return render(request, "events/form.html", {"form": form, "title": "New event"})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect("calendar")
    else:
        form = EventForm(instance=event)
    return render(
        request,
        "events/form.html",
        {"form": form, "title": "Edit event", "event": event},
    )


@login_required
@require_POST
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, user=request.user)
    event.delete()
    messages.success(request, "Event deleted.")
    return redirect("calendar")
