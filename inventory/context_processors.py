from django.conf import settings


def theme_names(request):
    return {
        "DAISYUI_LIGHT_THEME": getattr(settings, "DAISYUI_LIGHT_THEME", "light"),
        "DAISYUI_DARK_THEME": getattr(settings, "DAISYUI_DARK_THEME", "dark"),
    }
