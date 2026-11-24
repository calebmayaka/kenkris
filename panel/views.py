from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from website.models import Course, QuoteRequest, SiteSettings, Stat
from website.views import client_ip

from .models import must_change_password, require_password_change
from .forms import (
    CourseForm,
    InquiryUpdateForm,
    PanelLoginForm,
    PanelPasswordChangeForm,
    SiteSettingsForm,
    StatForm,
    UserCreateForm,
    UserEditForm,
)

User = get_user_model()

LOGIN_MAX_FAILURES = 10
LOGIN_LOCKOUT_SECONDS = 15 * 60


# --- Access control ----------------------------------------------------------

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Signed-in, active staff only. Signed-in non-staff get a 403."""

    def test_func(self):
        u = self.request.user
        return u.is_active and u.is_staff


class AdminRequiredMixin(StaffRequiredMixin):
    def test_func(self):
        return super().test_func() and self.request.user.is_superuser


# --- Auth ------------------------------------------------------------------

def _lock_key(request):
    return f"panel-login-fail:{client_ip(request)}"


class PanelLoginView(auth_views.LoginView):
    template_name = "panel/login.html"
    authentication_form = PanelLoginForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if cache.get(_lock_key(request), 0) >= LOGIN_MAX_FAILURES:
            return render(request, self.template_name, {
                "form": self.authentication_form(request),
                "locked": True,
            }, status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        key = _lock_key(self.request)
        cache.add(key, 0, timeout=LOGIN_LOCKOUT_SECONDS)
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=LOGIN_LOCKOUT_SECONDS)
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(_lock_key(self.request))
        return super().form_valid(form)


class PanelLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("panel:login")


class PanelPasswordChangeView(StaffRequiredMixin, auth_views.PasswordChangeView):
    template_name = "panel/password_change.html"
    form_class = PanelPasswordChangeForm
    success_url = reverse_lazy("panel:inquiries")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["forced"] = must_change_password(self.request.user)
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        require_password_change(self.request.user, required=False)
        messages.success(self.request, "Your password has been changed.")
        return response


# --- Inquiries -------------------------------------------------------------

class InquiryListView(StaffRequiredMixin, ListView):
    template_name = "panel/inquiry_list.html"
    context_object_name = "inquiries"
    paginate_by = 25

    def get_queryset(self):
        qs = QuoteRequest.objects.all()
        self.status = self.request.GET.get("status", "")
        self.q = self.request.GET.get("q", "").strip()
        if self.status in QuoteRequest.Status.values:
            qs = qs.filter(status=self.status)
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(email__icontains=self.q)
                           | Q(phone__icontains=self.q) | Q(message__icontains=self.q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        counts = dict(QuoteRequest.objects.values_list("status").annotate(n=Count("id")))
        ctx["tabs"] = [{"value": "", "label": "All", "count": sum(counts.values())}] + [
            {"value": v, "label": label, "count": counts.get(v, 0)} for v, label in QuoteRequest.Status.choices
        ]
        ctx["status"] = self.status
        ctx["q"] = self.q
        return ctx


class InquiryDetailView(StaffRequiredMixin, View):
    template_name = "panel/inquiry_detail.html"

    def get(self, request, pk):
        inquiry = get_object_or_404(QuoteRequest, pk=pk)
        return render(request, self.template_name, self.context(inquiry, InquiryUpdateForm(instance=inquiry)))

    def post(self, request, pk):
        inquiry = get_object_or_404(QuoteRequest, pk=pk)
        form = InquiryUpdateForm(request.POST, instance=inquiry)
        if form.is_valid():
            form.save()
            messages.success(request, "Inquiry updated.")
            return redirect("panel:inquiry_detail", pk=pk)
        return render(request, self.template_name, self.context(inquiry, form), status=400)

    @staticmethod
    def context(inquiry, form):
        digits = "".join(ch for ch in inquiry.phone if ch.isdigit())
        if digits.startswith("0") and len(digits) == 10:  # local Kenyan format 07xx...
            digits = "254" + digits[1:]
        return {"inquiry": inquiry, "form": form, "phone_digits": digits}


# --- Users -------------------------------------------------------------------

class UserListView(AdminRequiredMixin, ListView):
    template_name = "panel/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.order_by("-is_active", "-is_superuser", "first_name", "username")


class UserCreateView(AdminRequiredMixin, View):
    template_name = "panel/user_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": UserCreateForm(), "creating": True})

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            require_password_change(user)
            messages.success(request, f"User “{user.username}” created. Share the password with them securely — "
                                      "they'll be asked to choose their own when they first sign in.")
            return redirect("panel:users")
        return render(request, self.template_name, {"form": form, "creating": True}, status=400)


class UserEditView(AdminRequiredMixin, View):
    template_name = "panel/user_form.html"

    def get(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        return render(request, self.template_name, {"form": UserEditForm(instance=target, acting_user=request.user), "target": target})

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        form = UserEditForm(request.POST, instance=target, acting_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User “{target.username}” updated.")
            return redirect("panel:users")
        return render(request, self.template_name, {"form": form, "target": target}, status=400)


class UserSetPasswordView(AdminRequiredMixin, View):
    template_name = "panel/user_password.html"

    def get(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        return render(request, self.template_name, {"form": SetPasswordForm(target), "target": target})

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        form = SetPasswordForm(target, request.POST)
        if form.is_valid():
            form.save()
            if target == request.user:
                update_session_auth_hash(request, target)
                require_password_change(target, required=False)
                messages.success(request, "Your password has been set.")
            else:
                require_password_change(target)
                messages.success(request, f"Password for “{target.username}” has been set. "
                                          "They'll be asked to choose their own at next sign-in.")
            return redirect("panel:users")
        return render(request, self.template_name, {"form": form, "target": target}, status=400)


def index(request):
    return redirect("panel:inquiries")


# --- Content: courses, stats, site settings ------------------------------------



class ContentFormMixin(StaffRequiredMixin):
    """Shared create/edit behaviour for simple content objects."""

    template_name = "panel/object_form.html"
    noun = "item"
    list_url = None

    def get_success_url(self):
        return reverse_lazy(self.list_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(noun=self.noun, list_url=self.list_url, creating=self.object is None)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"{self.noun.capitalize()} saved.")
        return super().form_valid(form)


class ContentDeleteMixin(StaffRequiredMixin):
    template_name = "panel/confirm_delete.html"
    noun = "item"
    list_url = None

    def get_success_url(self):
        return reverse_lazy(self.list_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(noun=self.noun, list_url=self.list_url)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"{self.noun.capitalize()} deleted.")
        return super().form_valid(form)


class CourseListView(StaffRequiredMixin, View):
    def get(self, request):
        today = timezone.localdate()
        courses = Course.objects.all()
        upcoming = [c for c in courses if c.start_date >= today]
        return render(request, "panel/course_list.html", {
            "upcoming": upcoming,
            "on_site": [c for c in upcoming if c.is_published][:4],
            "past": sorted((c for c in courses if c.start_date < today), key=lambda c: c.start_date, reverse=True),
        })


class CourseCreateView(ContentFormMixin, CreateView):
    model, form_class, noun, list_url = Course, CourseForm, "course", "panel:courses"


class CourseEditView(ContentFormMixin, UpdateView):
    model, form_class, noun, list_url = Course, CourseForm, "course", "panel:courses"


class CourseDeleteView(ContentDeleteMixin, DeleteView):
    model, noun, list_url = Course, "course", "panel:courses"


class StatListView(StaffRequiredMixin, ListView):
    model = Stat
    template_name = "panel/stat_list.html"
    context_object_name = "stats"


class StatCreateView(ContentFormMixin, CreateView):
    model, form_class, noun, list_url = Stat, StatForm, "stat", "panel:stats"

    def get_initial(self):
        last = Stat.objects.order_by("-order").first()
        return {"order": (last.order + 1) if last else 0}


class StatEditView(ContentFormMixin, UpdateView):
    model, form_class, noun, list_url = Stat, StatForm, "stat", "panel:stats"


class StatDeleteView(ContentDeleteMixin, DeleteView):
    model, noun, list_url = Stat, "stat", "panel:stats"


class SiteSettingsView(AdminRequiredMixin, View):
    template_name = "panel/site_settings.html"

    def get(self, request):
        return render(request, self.template_name, {"form": SiteSettingsForm(instance=SiteSettings.load())})

    def post(self, request):
        form = SiteSettingsForm(request.POST, instance=SiteSettings.load())
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings saved. Changes are live on the website.")
            return redirect("panel:site_settings")
        return render(request, self.template_name, {"form": form}, status=400)
