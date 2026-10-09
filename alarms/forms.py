from django import forms

from .models import WEEKDAY_CHOICES, Alarm, AlarmMode


class AlarmForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Repeat on",
    )

    class Meta:
        model = Alarm
        fields = ["title", "time", "mode", "once_date", "enabled"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "mode": forms.Select(attrs={"class": "form-control"}),
            "once_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "enabled": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["weekdays"].initial = [str(day) for day in self.instance.weekday_list()]

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode")
        once_date = cleaned.get("once_date")
        weekdays = cleaned.get("weekdays") or []

        if mode == AlarmMode.ONCE and not once_date:
            self.add_error("once_date", "Choose a date for a one-time alarm.")
        if mode == AlarmMode.WEEKLY and not weekdays:
            self.add_error("weekdays", "Select at least one weekday.")
        return cleaned

    def save(self, commit=True):
        alarm = super().save(commit=False)
        if alarm.mode == AlarmMode.WEEKLY:
            alarm.set_weekdays([int(day) for day in self.cleaned_data.get("weekdays") or []])
            alarm.once_date = None
        else:
            alarm.weekdays = ""
        if commit:
            alarm.save()
        return alarm
