import datetime

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Course, QuoteRequest, SiteSettings, Stat

VALID = {"name": "Jane Importer", "email": "jane@example.com", "phone": "+254 700 000000",
         "message": "1x40ft container of machinery, Mombasa to Nairobi"}


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", QUOTE_RATE_LIMIT_PER_HOUR=3,
                   SECURE_SSL_REDIRECT=False)
class QuoteFormTests(TestCase):
    def setUp(self):
        cache.clear()
        settings_row = SiteSettings.load()
        settings_row.quote_notify_email = "office@example.com"
        settings_row.save()

    def test_valid_submission_saves_and_emails(self):
        resp = self.client.post(reverse("website:submit_quote"), VALID)
        self.assertRedirects(resp, reverse("website:index") + "?sent=1#contact", fetch_redirect_response=False)
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.email, "jane@example.com")
        self.assertTrue(quote.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["office@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["jane@example.com"])

    def test_success_message_shown_after_redirect(self):
        resp = self.client.post(reverse("website:submit_quote"), VALID, follow=True)
        self.assertContains(resp, "we’ve received your request")

    def test_invalid_submission_shows_errors_and_saves_nothing(self):
        resp = self.client.post(reverse("website:submit_quote"), {**VALID, "email": "not-an-email"})
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "Please check the highlighted fields", status_code=400)
        self.assertFalse(QuoteRequest.objects.exists())

    def test_honeypot_drops_submission_silently(self):
        resp = self.client.post(reverse("website:submit_quote"), {**VALID, "website": "http://spam"})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(QuoteRequest.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit(self):
        for _ in range(3):
            self.client.post(reverse("website:submit_quote"), VALID)
        self.client.post(reverse("website:submit_quote"), VALID)
        self.assertEqual(QuoteRequest.objects.count(), 3)

    def test_email_failure_still_saves_lead(self):
        with override_settings(EMAIL_BACKEND="website.tests.BrokenBackend"):
            self.client.post(reverse("website:submit_quote"), VALID)
        quote = QuoteRequest.objects.get()
        self.assertFalse(quote.email_sent)

    def test_get_not_allowed_on_quote_endpoint(self):
        self.assertEqual(self.client.get(reverse("website:submit_quote")).status_code, 405)


class BrokenBackend:
    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, messages):
        raise ConnectionRefusedError("SMTP down")


@override_settings(SECURE_SSL_REDIRECT=False)
class PageTests(TestCase):
    def test_home_renders_content_from_db(self):
        SiteSettings.load()
        Stat.objects.create(value="9,999+", label="Test Stat", show_in_hero=True)
        resp = self.client.get(reverse("website:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cargo from anywhere")
        self.assertContains(resp, "9,999+", count=2)  # hero + stats grid
        self.assertContains(resp, "info@kenkrislogistics.co.ke")
        self.assertNotContains(resp, "Claude Design")

    def test_only_upcoming_published_courses_shown(self):
        today = timezone.localdate()
        Course.objects.create(name="Past Course", start_date=today - datetime.timedelta(days=1))
        Course.objects.create(name="Hidden Course", start_date=today + datetime.timedelta(days=5), is_published=False)
        Course.objects.create(name="Future Course", start_date=today + datetime.timedelta(days=5))
        resp = self.client.get(reverse("website:index"))
        self.assertContains(resp, "Future Course")
        self.assertNotContains(resp, "Past Course")
        self.assertNotContains(resp, "Hidden Course")

    def test_empty_courses_message(self):
        resp = self.client.get(reverse("website:index"))
        self.assertContains(resp, "New course dates are coming soon")

    def test_site_settings_is_singleton(self):
        SiteSettings(header_phone="1").save()
        SiteSettings(header_phone="2").save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().header_phone, "2")

    def test_whatsapp_link(self):
        s = SiteSettings(whatsapp_number="+254 797 721 062")
        self.assertTrue(s.whatsapp_url.startswith("https://wa.me/254797721062?text="))
        resp = self.client.get(reverse("website:index"))
        self.assertContains(resp, "https://wa.me/254797721062")

    def test_whatsapp_button_hidden_when_blank(self):
        site = SiteSettings.load()
        site.whatsapp_number = ""
        site.save()
        self.assertEqual(site.whatsapp_url, "")
        self.assertNotContains(self.client.get(reverse("website:index")), "wa.me")

    def test_header_phone_href(self):
        s = SiteSettings(header_phone="+254 797 721 062, +254 735 163 720")
        self.assertEqual(s.header_phone_href, "tel:+254797721062")


@override_settings(SECURE_SSL_REDIRECT=False, SITE_URL="https://kenkrislogistics.co.ke")
class SeoTests(TestCase):
    def test_canonical_ignores_query_string(self):
        resp = self.client.get("/?sent=1")
        self.assertContains(resp, '<link rel="canonical" href="https://kenkrislogistics.co.ke/">')
        self.assertNotContains(resp, "sent=1\"")

    def test_meta_and_social_tags(self):
        resp = self.client.get("/")
        self.assertContains(resp, "<title>Customs Clearing Agent in Nairobi")
        self.assertContains(resp, 'property="og:image" content="https://kenkrislogistics.co.ke/static/website/img/og-image')
        self.assertContains(resp, 'name="twitter:card" content="summary_large_image"')
        self.assertContains(resp, 'name="robots" content="index, follow')

    def test_structured_data_is_valid_json(self):
        import json
        import re
        html = self.client.get("/").content.decode()
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        data = json.loads(block)
        types = {node["@type"] for node in data["@graph"]}
        self.assertEqual(types, {"Organization", "LocalBusiness", "WebSite"})
        business = next(n for n in data["@graph"] if n["@type"] == "LocalBusiness")
        self.assertEqual(len(business["hasOfferCatalog"]["itemListElement"]), 4)

    def test_robots_txt(self):
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp["Content-Type"], "text/plain; charset=utf-8")
        body = resp.content.decode()
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Sitemap: https://kenkrislogistics.co.ke/sitemap.xml", body)

    def test_sitemap(self):
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp["Content-Type"])
        self.assertContains(resp, "<loc>https://kenkrislogistics.co.ke/</loc>")
        self.assertNotContains(resp, "/admin")

    def test_manifest_and_icon_redirects(self):
        self.assertEqual(self.client.get("/site.webmanifest").json()["short_name"], "KenKris")
        for path in ["/favicon.ico", "/apple-touch-icon.png"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 301)
            self.assertIn("/static/website/img/", resp["Location"])

    def test_branded_404_is_noindex(self):
        resp = self.client.get("/no-such-page/")
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "gone off-route", status_code=404)
        self.assertContains(resp, '<meta name="robots" content="noindex">', status_code=404)
