"""Seed the content from the original design so the site isn't empty on first deploy.

The original courses ran Aug–Sep 2026 and are already past, so they're seeded
for reference but won't appear on the site until staff add new dates in admin.
"""

import datetime

from django.db import migrations

STATS = [
    # value, label, show_in_hero
    ("2,000+", "Consignments Cleared", True),
    ("98%", "On-time Clearance", False),
    ("4", "Border Corridors", True),
    ("12+", "Years of Experience", True),
]

COURSES = [
    ("Customs Clearance Basics", datetime.date(2026, 8, 12)),
    ("HS Classification Workshop", datetime.date(2026, 8, 26)),
    ("Freight Documentation", datetime.date(2026, 9, 9)),
    ("Trade Compliance for SMEs", datetime.date(2026, 9, 23)),
]


def seed(apps, schema_editor):
    SiteSettings = apps.get_model("website", "SiteSettings")
    Stat = apps.get_model("website", "Stat")
    Course = apps.get_model("website", "Course")

    SiteSettings.objects.get_or_create(pk=1)
    if not Stat.objects.exists():
        for i, (value, label, hero) in enumerate(STATS):
            Stat.objects.create(value=value, label=label, show_in_hero=hero, order=i)
    if not Course.objects.exists():
        for name, date in COURSES:
            Course.objects.create(name=name, start_date=date)


class Migration(migrations.Migration):
    dependencies = [("website", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
