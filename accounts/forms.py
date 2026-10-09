from zoneinfo import available_timezones

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import RegistrationStatus, Theme, UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    timezone = forms.ChoiceField(choices=[])

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "timezone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tz_choices = [(tz, tz) for tz in sorted(available_timezones())]
        self.fields["timezone"].choices = tz_choices
        self.fields["timezone"].initial = "UTC"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists "
                "(including pending or denied registrations)."
            )
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken "
                "(including pending or denied registrations)."
            )
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.is_active = False
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.timezone = self.cleaned_data["timezone"]
            profile.registration_status = RegistrationStatus.PENDING
            profile.save()
        return user


class ApprovedAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def confirm_login_allowed(self, user):
        if user.is_superuser:
            return
        profile = getattr(user, "profile", None)
        if profile is None:
            raise forms.ValidationError("Account profile is missing.", code="no_profile")
        if profile.registration_status == RegistrationStatus.PENDING:
            raise forms.ValidationError(
                "Your registration is pending approval.",
                code="pending",
            )
        if profile.registration_status == RegistrationStatus.DENIED:
            raise forms.ValidationError(
                "Your registration was denied. You cannot sign in.",
                code="denied",
            )
        if not user.is_active or not profile.is_approved:
            raise forms.ValidationError(
                "This account is not active.",
                code="inactive",
            )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("theme", "timezone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tz_choices = [(tz, tz) for tz in sorted(available_timezones())]
        self.fields["timezone"].widget = forms.Select(choices=tz_choices)
        self.fields["theme"].widget = forms.Select(choices=Theme.choices)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
