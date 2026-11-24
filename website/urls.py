from django.templatetags.static import static
from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = "website"

urlpatterns = [
    path("", views.index, name="index"),
    path("quote/", views.submit_quote, name="submit_quote"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("site.webmanifest", views.web_manifest, name="web_manifest"),
    # Browsers and crawlers request these at the root regardless of <link> tags.
    path("favicon.ico", RedirectView.as_view(url=static("website/img/favicon.ico"), permanent=True)),
    path("apple-touch-icon.png", RedirectView.as_view(url=static("website/img/apple-touch-icon.png"), permanent=True)),
]
