from django.conf import settings

from .models import SiteSettings


def site_settings(request):
    return {"site": SiteSettings.load()}


def seo(request):
    return {"SITE_URL": settings.SITE_URL}
