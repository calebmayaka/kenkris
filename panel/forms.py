from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from website.models import Course, QuoteRequest, SiteSettings, Stat

User = get_user_model()

ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_CHOICES = [
    (ROLE_STAFF, "Staff — can view and update inquiries"),
    (ROLE_ADMIN, "Administrator — inquiries and user management"),
]


def role_of(user):
    return ROLE_ADMIN if user.is_superuser else ROLE_STAFF


def apply_role(user, role):
    user.is_staff = True  # everyone created here can use the panel
    user.is_superuser = role == ROLE_ADMIN


class PanelLoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Incorrect username or password.",
        "no_access": "This account doesn't have access to the admin panel.",
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(self.error_messages["no_access"], code="no_access")


class EmailUniqueMixin:
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Another user already has this email address.")
        return email


class UserCreateForm(EmailUniqueMixin, UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=ROLE_STAFF, widget=forms.RadioSelect)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["first_name", "last_name", "username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["first_name", "last_name", "email"]:
            self.fields[name].required = True
        # Django 5.1+ adds a "usable_password" toggle; every panel user needs a password.
        self.fields.pop("usable_password", None)

    def save(self, commit=True):
        user = super().save(commit=False)
        apply_role(user, self.cleaned_data["role"])
        if commit:
            user.save()
        return user


class UserEditForm(EmailUniqueMixin, forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        labels = {"is_active": "Account active (untick to block sign-in)"}

    def __init__(self, *args, acting_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.acting_user = acting_user
        self.fields["role"].initial = role_of(self.instance)
        for name in ["first_name", "last_name", "email"]:
            self.fields[name].required = True

    def clean(self):
        cleaned = super().clean()
        user = self.instance
        demoting = cleaned.get("role") != ROLE_ADMIN
        deactivating = not cleaned.get("is_active", True)

        if user == self.acting_user:
            if deactivating:
                self.add_error("is_active", "You can't deactivate your own account.")
            if demoting:
                self.add_error("role", "You can't remove your own administrator role.")

        if user.is_superuser and (demoting or deactivating):
            other_admins = User.objects.filter(is_superuser=True, is_active=True).exclude(pk=user.pk)
            if not other_admins.exists():
                raise forms.ValidationError("This is the only active administrator. Make someone else an administrator first.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        apply_role(user, self.cleaned_data["role"])
        if commit:
            user.save()
        return user


class InquiryUpdateForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ["status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 5, "placeholder": "Internal notes — e.g. called, sent quote, follow up Friday"})}


# --- Content -------------------------------------------------------------------


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["header_phone", "whatsapp_number", "contact_phone", "contact_email",
                  "contact_address", "contact_hours", "quote_notify_email"]
        labels = {
            "header_phone": "Header phone",
            "whatsapp_number": "WhatsApp number",
            "contact_phone": "Contact phone(s)",
            "contact_email": "Contact email",
            "contact_address": "Office address",
            "contact_hours": "Opening hours",
            "quote_notify_email": "Send quote requests to",
        }


class StatForm(forms.ModelForm):
    class Meta:
        model = Stat
        fields = ["value", "label", "show_in_hero", "order"]
        labels = {"value": "Figure", "show_in_hero": "Also show in the top banner",
                  "order": "Position (lower numbers first)"}


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "start_date", "is_published"]
        labels = {"name": "Course name", "is_published": "Published (show on the website)"}
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
        help_texts = {"start_date": "Courses disappear from the website automatically after this date. "
                                    "The website shows the next 4."}


class PanelPasswordChangeForm(PasswordChangeForm):
    def clean(self):
        cleaned = super().clean()
        new = cleaned.get("new_password2")
        if new and "new_password2" not in self.errors and self.user.check_password(new):
            self.add_error("new_password2", "Choose a password different from your current one.")
        return cleaned
