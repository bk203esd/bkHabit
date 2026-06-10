from django import forms

from .models import Habit


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ["name", "description", "frequency", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "frequency": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }