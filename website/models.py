from urllib.parse import quote

from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    """Single row of contact details shown across the site (header, contact, footer)."""

    header_phone = models.CharField(
        max_length=100,
        default="+254 797 721 062",
        help_text="Shown in the header. The first number becomes the click-to-call link.",
    )
    whatsapp_number = models.CharField(
        max_length=30,
        blank=True,
        default="+254 797 721 062",
        help_text="Number for the WhatsApp button in the header, with country code. Leave blank to hide the button.",
    )
    contact_phone = models.CharField(max_length=150, default="+254 797 721 062, +254 735 163 720")
    contact_email = models.EmailField(default="info@kenkrislogistics.co.ke")
    contact_address = models.CharField(max_length=200, default="Mombasa Road, Nairobi, Kenya")
    contact_hours = models.CharField(max_length=100, default="Mon – Sat, 8am – 6pm EAT")
    quote_notify_email = models.EmailField(
        blank=True,
        help_text="Where new quote requests are emailed. Leave blank to use the contact email.",
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce a single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def header_phone_href(self):
        first = self.header_phone.split(",")[0]
        return "tel:" + "".join(first.split())

    @property
    def whatsapp_url(self):
        """wa.me link: digits only, no '+' or spaces (e.g. https://wa.me/254797721062)."""
        digits = "".join(ch for ch in self.whatsapp_number if ch.isdigit())
        if not digits:
            return ""
        return f"https://wa.me/{digits}?text=" + quote("Hello KenKris Logistics, I'd like to enquire about")

    @property
    def notify_email(self):
        return self.quote_notify_email or self.contact_email


class Stat(models.Model):
    value = models.CharField(max_length=20, help_text='e.g. "2,000+" or "98%"')
    label = models.CharField(max_length=60)
    show_in_hero = models.BooleanField(default=False, help_text="Also show this figure in the top banner.")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.value} {self.label}"


class CourseQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(is_published=True, start_date__gte=timezone.localdate())


class Course(models.Model):
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    is_published = models.BooleanField(default=True)

    objects = CourseQuerySet.as_manager()

    class Meta:
        ordering = ["start_date", "name"]

    def __str__(self):
        return f"{self.name} ({self.start_date:%d %b %Y})"


class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        WON = "won", "Won"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField("What are you shipping?", max_length=5000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True, help_text="Internal notes (not visible to the customer).")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    email_sent = models.BooleanField(default=False, help_text="Whether the notification email went out.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} – {self.created_at:%d %b %Y %H:%M}"
