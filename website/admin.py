from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import Course, QuoteRequest, SiteSettings, Stat


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Header", {"fields": ["header_phone", "whatsapp_number"]}),
        ("Contact details", {"fields": ["contact_phone", "contact_email", "contact_address", "contact_hours"]}),
        ("Quote notifications", {"fields": ["quote_notify_email"]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip the one-row list and go straight to the edit form.
        obj = SiteSettings.load()
        return redirect(reverse("admin:website_sitesettings_change", args=[obj.pk]))


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ["value", "label", "show_in_hero", "order"]
    list_editable = ["show_in_hero", "order"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "is_published"]
    list_editable = ["is_published"]
    list_filter = ["is_published"]
    date_hierarchy = "start_date"


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "status", "email_sent", "created_at"]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]
    search_fields = ["name", "email", "phone", "message"]
    readonly_fields = ["name", "email", "phone", "message", "ip_address", "email_sent", "created_at"]
    fields = ["name", "email", "phone", "message", "status", "notes", "created_at", "ip_address", "email_sent"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
