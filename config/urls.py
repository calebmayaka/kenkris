from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "KenKris Logistics"
admin.site.site_title = "KenKris Admin"
admin.site.index_title = "Website content"
# Hidden Django admin: superusers only.
admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser

urlpatterns = [
    path("admin/", include("panel.urls")),
    path("", include("website.urls")),
]

if settings.ADMIN_URL:
    urlpatterns.insert(0, path(settings.ADMIN_URL, admin.site.urls))
