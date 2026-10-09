from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from django.contrib.auth.models import User
        from django.db.models.signals import post_save

        from .models import RegistrationStatus, UserProfile

        def ensure_profile(sender, instance, created, **kwargs):
            if created and not hasattr(instance, "profile"):
                status = (
                    RegistrationStatus.APPROVED
                    if instance.is_superuser
                    else RegistrationStatus.PENDING
                )
                UserProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        "registration_status": status,
                        "timezone": "UTC",
                    },
                )
                if instance.is_superuser and not instance.is_active:
                    instance.is_active = True
                    instance.save(update_fields=["is_active"])

        post_save.connect(ensure_profile, sender=User)
