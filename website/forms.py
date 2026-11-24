from django import forms

from .models import QuoteRequest


class QuoteRequestForm(forms.ModelForm):
    # Honeypot: hidden from people with CSS; bots that fill every field get dropped.
    website = forms.CharField(required=False, label="Leave this empty")

    class Meta:
        model = QuoteRequest
        fields = ["name", "email", "phone", "message"]
        labels = {"name": "Full name", "email": "Email", "phone": "Phone"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
