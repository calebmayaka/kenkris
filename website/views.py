import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from . import content
from .forms import QuoteRequestForm
from .models import Course, SiteSettings, Stat

logger = logging.getLogger(__name__)


def client_ip(request):
    """The visitor's real IP.

    Caddy sets X-Real-IP from Cloudflare's CF-Connecting-IP, and only trusts
    that header on connections from Cloudflare's IP ranges (see
    deploy/Caddyfile), so clients can't spoof it. Gunicorn listens on
    localhost only, so nothing else can reach Django directly.
    Falls back to REMOTE_ADDR in development.
    """
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


def rate_limited(ip):
    """True once an IP exceeds the hourly quote limit."""
    if not ip:
        return False
    key = f"quote-rate:{ip}"
    cache.add(key, 0, timeout=3600)
    try:
        count = cache.incr(key)
    except ValueError:  # key expired between add and incr
        cache.set(key, 1, timeout=3600)
        count = 1
    return count > settings.QUOTE_RATE_LIMIT_PER_HOUR


def page_context(form=None):
    stats = list(Stat.objects.all())
    return {
        "form": form or QuoteRequestForm(),
        "stats": stats,
        "hero_stats": [s for s in stats if s.show_in_hero],
        "courses": Course.objects.upcoming()[:4],
        "tracker_steps": content.TRACKER_STEPS,
        "strip_chips": content.STRIP_CHIPS,
        "services": content.SERVICES,
        "journey_steps": content.JOURNEY_STEPS,
        "features": content.FEATURES,
        "why_points": content.WHY_POINTS,
        "corridors": content.CORRIDORS,
        "destinations": content.DESTINATIONS,
        "requirements": content.REQUIREMENTS,
    }


@require_http_methods(["GET", "HEAD"])
def index(request):
    return render(request, "website/index.html", page_context())


def notify_office(quote):
    site = SiteSettings.load()
    recipient = site.notify_email or settings.QUOTE_NOTIFY_EMAIL
    if not recipient:
        return False
    if not settings.EMAIL_HOST and "locmem" not in settings.EMAIL_BACKEND:
        # No SMTP configured: the email would only go to the log, so don't
        # mark it as sent. Staff will see it unflagged in the admin.
        logger.warning("SMTP not configured; quote %s saved but not emailed", quote.pk)
        return False
    body = (
        f"New quote request from the website\n\n"
        f"Name:  {quote.name}\n"
        f"Email: {quote.email}\n"
        f"Phone: {quote.phone or '-'}\n\n"
        f"What are they shipping?\n{quote.message}\n"
    )
    email = EmailMessage(
        subject=f"Quote request: {quote.name}",
        body=body,
        to=[recipient],
        reply_to=[quote.email],
    )
    try:
        email.send(fail_silently=False)
        return True
    except Exception:
        # The request is already saved; never lose a lead over an email error.
        logger.exception("Failed to send quote notification for QuoteRequest %s", quote.pk)
        return False


@require_POST
def submit_quote(request):
    form = QuoteRequestForm(request.POST)
    if not form.is_valid():
        response = render(request, "website/index.html", page_context(form))
        response.status_code = 400
        return response

    success_url = reverse("website:index") + "?sent=1#contact"

    if form.is_spam():
        # Pretend it worked so bots don't learn to avoid the honeypot.
        return redirect(success_url)

    ip = client_ip(request)
    if rate_limited(ip):
        messages.error(request, "Too many requests from your connection. Please call or email us instead.")
        return redirect(reverse("website:index") + "#contact")

    quote = form.save(commit=False)
    quote.ip_address = ip
    quote.save()
    quote.email_sent = notify_office(quote)
    quote.save(update_fields=["email_sent"])

    messages.success(request, "Thanks — we’ve received your request and will be in touch within one business day.")
    return redirect(success_url)


# --- SEO endpoints -----------------------------------------------------------

@require_http_methods(["GET", "HEAD"])
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /quote/",
        "",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_http_methods(["GET", "HEAD"])
def sitemap_xml(request):
    return render(request, "website/sitemap.xml", {"base": settings.SITE_URL},
                  content_type="application/xml; charset=utf-8")


@require_http_methods(["GET", "HEAD"])
def web_manifest(request):
    return JsonResponse({
        "name": "KenKris Logistics",
        "short_name": "KenKris",
        "description": "Customs clearing, freight forwarding and cargo handling in Kenya.",
        "start_url": "/",
        "display": "browser",
        "background_color": "#F5F7FA",
        "theme_color": "#0B2452",
        "icons": [
            {"src": static("website/img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("website/img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
        ],
    }, content_type="application/manifest+json")
