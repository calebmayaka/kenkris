from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from website.models import QuoteRequest

User = get_user_model()
PW = "Corr3ct-Horse-Battery"


@override_settings(SECURE_SSL_REDIRECT=False)
class PanelTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user("boss", "boss@example.com", PW, is_staff=True, is_superuser=True)
        self.staff = User.objects.create_user("clerk", "clerk@example.com", PW, is_staff=True)
        self.outsider = User.objects.create_user("visitor", "v@example.com", PW)
        self.quote = QuoteRequest.objects.create(name="Jane Importer", email="jane@example.com",
                                                 phone="0712345678", message="2 pallets of tiles")


class AccessTests(PanelTestCase):
    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("panel:inquiries"))
        self.assertRedirects(resp, reverse("panel:login") + "?next=" + reverse("panel:inquiries"))

    def test_login_page_renders(self):
        self.assertContains(self.client.get(reverse("panel:login")), "Sign in")

    def test_non_staff_cannot_sign_in(self):
        resp = self.client.post(reverse("panel:login"), {"username": "visitor", "password": PW})
        self.assertContains(resp, "doesn&#x27;t have access")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_sees_inquiries_but_not_users(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("panel:inquiries")), "Jane Importer")
        self.assertEqual(self.client.get(reverse("panel:users")).status_code, 403)
        self.assertEqual(self.client.get(reverse("panel:user_create")).status_code, 403)

    def test_admin_sees_users(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("panel:users")), "clerk")

    def test_login_lockout_after_repeated_failures(self):
        for _ in range(10):
            self.client.post(reverse("panel:login"), {"username": "boss", "password": "wrong"})
        resp = self.client.post(reverse("panel:login"), {"username": "boss", "password": PW})
        self.assertEqual(resp.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_successful_login_lands_on_inquiries(self):
        resp = self.client.post(reverse("panel:login"), {"username": "clerk", "password": PW}, follow=True)
        self.assertContains(resp, "Jane Importer")

    def test_logout_requires_post(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("panel:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_django_admin_superuser_only(self):
        from django.contrib import admin
        req = type("R", (), {"user": self.staff})()
        self.assertFalse(admin.site.has_permission(req))
        req.user = self.admin
        self.assertTrue(admin.site.has_permission(req))


class InquiryTests(PanelTestCase):
    def test_filter_and_search(self):
        QuoteRequest.objects.create(name="Old Lead", email="o@example.com", message="x", status="closed")
        self.client.force_login(self.staff)
        resp = self.client.get(reverse("panel:inquiries"), {"status": "closed"})
        self.assertContains(resp, "Old Lead")
        self.assertNotContains(resp, "Jane Importer")
        resp = self.client.get(reverse("panel:inquiries"), {"q": "tiles"})
        self.assertContains(resp, "Jane Importer")
        self.assertNotContains(resp, "Old Lead")

    def test_update_status_and_notes(self):
        self.client.force_login(self.staff)
        url = reverse("panel:inquiry_detail", args=[self.quote.pk])
        resp = self.client.get(url)
        self.assertContains(resp, "https://wa.me/254712345678")  # 07... normalised to 2547...
        self.client.post(url, {"status": "contacted", "notes": "Called, sending quote"})
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "contacted")
        self.assertEqual(self.quote.notes, "Called, sending quote")


class UserManagementTests(PanelTestCase):
    def test_create_staff_user(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("panel:user_create"), {
            "first_name": "Mary", "last_name": "Wanjiku", "username": "mary", "email": "Mary@Example.com",
            "role": "staff", "password1": PW, "password2": PW,
        })
        self.assertRedirects(resp, reverse("panel:users"))
        mary = User.objects.get(username="mary")
        self.assertTrue(mary.is_staff)
        self.assertFalse(mary.is_superuser)
        self.assertEqual(mary.email, "mary@example.com")
        self.assertTrue(mary.check_password(PW))

    def test_create_rejects_weak_password_and_duplicate_email(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("panel:user_create"), {
            "first_name": "A", "last_name": "B", "username": "ab", "email": "clerk@example.com",
            "role": "staff", "password1": "123", "password2": "123",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "already has this email", status_code=400)
        self.assertFalse(User.objects.filter(username="ab").exists())

    def test_staff_cannot_create_users(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse("panel:user_create"), {
            "first_name": "X", "last_name": "Y", "username": "sneaky", "email": "s@example.com",
            "role": "admin", "password1": PW, "password2": PW,
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(User.objects.filter(username="sneaky").exists())

    def test_admin_cannot_deactivate_or_demote_self(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("panel:user_edit", args=[self.admin.pk]), {
            "first_name": "B", "last_name": "B", "email": "boss@example.com", "role": "staff",
        })
        self.assertEqual(resp.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser and self.admin.is_active)

    def test_promote_and_deactivate_other_user(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("panel:user_edit", args=[self.staff.pk]), {
            "first_name": "C", "last_name": "L", "email": "clerk@example.com", "role": "admin", "is_active": "on",
        })
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_superuser)
        self.client.post(reverse("panel:user_edit", args=[self.staff.pk]), {
            "first_name": "C", "last_name": "L", "email": "clerk@example.com", "role": "staff",
        })
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_active)

    def test_set_password(self):
        self.client.force_login(self.admin)
        new = "An0ther-Strong-Pass"
        self.client.post(reverse("panel:user_password", args=[self.staff.pk]), {"new_password1": new, "new_password2": new})
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password(new))


class ContentTests(PanelTestCase):
    def test_course_crud_shows_on_website(self):
        import datetime
        from django.utils import timezone
        from website.models import Course
        self.client.force_login(self.staff)
        date = (timezone.localdate() + datetime.timedelta(days=10)).isoformat()
        resp = self.client.post(reverse("panel:course_create"), {"name": "Incoterms Masterclass", "start_date": date, "is_published": "on"})
        self.assertRedirects(resp, reverse("panel:courses"))
        course = Course.objects.get(name="Incoterms Masterclass")
        self.assertContains(self.client.get(reverse("panel:courses")), "Showing")
        self.assertContains(self.client.get("/"), "Incoterms Masterclass")

        self.client.post(reverse("panel:course_edit", args=[course.pk]), {"name": "Incoterms Masterclass", "start_date": date})
        self.assertNotContains(self.client.get("/"), "Incoterms Masterclass")  # unpublished

        self.assertContains(self.client.get(reverse("panel:course_delete", args=[course.pk])), "can't be undone")
        self.client.post(reverse("panel:course_delete", args=[course.pk]))
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    def test_stat_crud(self):
        from website.models import Stat
        self.client.force_login(self.staff)
        self.client.post(reverse("panel:stat_create"), {"value": "500+", "label": "Happy Clients", "show_in_hero": "on", "order": "9"})
        stat = Stat.objects.get(label="Happy Clients")
        self.assertTrue(stat.show_in_hero)
        self.assertContains(self.client.get("/"), "500+", count=2)  # banner + grid
        self.client.post(reverse("panel:stat_edit", args=[stat.pk]), {"value": "600+", "label": "Happy Clients", "order": "9"})
        stat.refresh_from_db()
        self.assertEqual((stat.value, stat.show_in_hero), ("600+", False))
        self.client.post(reverse("panel:stat_delete", args=[stat.pk]))
        self.assertFalse(Stat.objects.filter(pk=stat.pk).exists())

    def test_site_settings_admin_only_and_live(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("panel:site_settings")).status_code, 403)
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("panel:site_settings"), {
            "header_phone": "+254 700 111 222", "whatsapp_number": "+254 700 111 222",
            "contact_phone": "+254 700 111 222", "contact_email": "hello@kenkrislogistics.co.ke",
            "contact_address": "Mombasa Road, Nairobi", "contact_hours": "Mon – Fri", "quote_notify_email": "",
        })
        self.assertRedirects(resp, reverse("panel:site_settings"))
        home = self.client.get("/")
        self.assertContains(home, "hello@kenkrislogistics.co.ke")
        self.assertContains(home, "https://wa.me/254700111222")

    def test_staff_sidebar_hides_admin_sections(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse("panel:courses"))
        self.assertContains(resp, "Stats")
        self.assertNotContains(resp, reverse("panel:site_settings"))
        self.assertNotContains(resp, reverse("panel:users"))


class FirstLoginPasswordTests(PanelTestCase):
    NEW = "My-Own-Strong-Pass-1"

    def _create_via_panel(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("panel:user_create"), {
            "first_name": "Ken", "last_name": "S", "username": "ken2", "email": "ken2@example.com",
            "role": "staff", "password1": PW, "password2": PW,
        })
        self.client.logout()
        return User.objects.get(username="ken2")

    def test_new_user_forced_to_change_password_on_first_login(self):
        user = self._create_via_panel()
        resp = self.client.post(reverse("panel:login"), {"username": "ken2", "password": PW})
        self.assertEqual(resp.status_code, 302)
        # Every panel page redirects to the change-password page...
        for name in ["panel:inquiries", "panel:courses", "panel:stats"]:
            self.assertRedirects(self.client.get(reverse(name)), reverse("panel:password_change"))
        self.assertContains(self.client.get(reverse("panel:password_change")), "Choose your own password")
        # ...until they set their own.
        resp = self.client.post(reverse("panel:password_change"), {
            "old_password": PW, "new_password1": self.NEW, "new_password2": self.NEW})
        self.assertRedirects(resp, reverse("panel:inquiries"))
        self.assertEqual(self.client.get(reverse("panel:inquiries")).status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.NEW))

    def test_cannot_reuse_temporary_password(self):
        self._create_via_panel()
        self.client.post(reverse("panel:login"), {"username": "ken2", "password": PW})
        resp = self.client.post(reverse("panel:password_change"), {
            "old_password": PW, "new_password1": PW, "new_password2": PW})
        self.assertContains(resp, "different from your current one")
        self.assertRedirects(self.client.get(reverse("panel:inquiries")), reverse("panel:password_change"))

    def test_admin_setting_password_flags_user(self):
        from panel.models import must_change_password
        self.client.force_login(self.admin)
        self.client.post(reverse("panel:user_password", args=[self.staff.pk]),
                         {"new_password1": self.NEW, "new_password2": self.NEW})
        self.assertTrue(must_change_password(self.staff))
        self.assertFalse(must_change_password(self.admin))

    def test_logout_allowed_while_change_pending(self):
        self._create_via_panel()
        self.client.post(reverse("panel:login"), {"username": "ken2", "password": PW})
        self.client.post(reverse("panel:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_public_site_unaffected(self):
        self._create_via_panel()
        self.client.post(reverse("panel:login"), {"username": "ken2", "password": PW})
        self.assertEqual(self.client.get("/").status_code, 200)
