from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from .models import Theme


def user_preferences(request):
    theme = Theme.LIGHT
    user_tz = "UTC"
    profile = None

    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile is not None:
            theme = profile.theme
            user_tz = profile.timezone or "UTC"
            try:
                timezone.activate(ZoneInfo(user_tz))
            except ZoneInfoNotFoundError:
                timezone.activate(ZoneInfo("UTC"))
                user_tz = "UTC"

    return {
        "user_theme": theme,
        "user_timezone": user_tz,
        "user_profile": profile,
    }
