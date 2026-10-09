from django import forms

from .models import WEEKDAY_CHOICES, Event, RecurrenceType


class EventForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Repeat on",
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "start",
            "end",
            "all_day",
            "recurrence_type",
            "recurrence_until",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "start": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "all_day": forms.CheckboxInput(attrs={"class": "form-check"}),
            "recurrence_type": forms.Select(attrs={"class": "form-control"}),
            "recurrence_until": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        self.fields["end"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        if self.instance and self.instance.pk:
            self.fields["weekdays"].initial = [
                str(day) for day in self.instance.weekday_list()
            ]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start")
        end = cleaned.get("end")
        recurrence_type = cleaned.get("recurrence_type")
        weekdays = cleaned.get("weekdays") or []

        if start and end and end < start:
            self.add_error("end", "End must be after start.")

        if recurrence_type == RecurrenceType.WEEKLY and not weekdays:
            self.add_error("weekdays", "Select at least one weekday for weekly events.")

        return cleaned

    def save(self, commit=True):
        event = super().save(commit=False)
        weekdays = [int(day) for day in self.cleaned_data.get("weekdays") or []]
        if event.recurrence_type == RecurrenceType.WEEKLY:
            event.set_weekdays(weekdays)
        else:
            event.recurrence_weekdays = ""
        if commit:
            event.save()
        return event
