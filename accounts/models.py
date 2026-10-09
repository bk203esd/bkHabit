from django.conf import settings
from django.db import models
from django.utils import timezone


class Theme(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"
    KAWAII = "kawaii", "Kawaii"


class RegistrationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    DENIED = "denied", "Denied"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    theme = models.CharField(
        max_length=20,
        choices=Theme.choices,
        default=Theme.LIGHT,
    )
    timezone = models.CharField(max_length=64, default="UTC")
    registration_status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_registrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.registration_status})"

    @property
    def is_approved(self) -> bool:
        return self.registration_status == RegistrationStatus.APPROVED

    def approve(self, reviewer) -> None:
        self.registration_status = RegistrationStatus.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.save()

    def deny(self, reviewer) -> None:
        self.registration_status = RegistrationStatus.DENIED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.save()
