# Data migration to seed the default footer navigation columns and links.
from django.db import migrations


def seed_footer_navigation(apps, schema_editor):
    """
    Create the default footer columns and links matching the current frontend footer.
    The 'Social' column is powered by the SocialNetwork model and is not seeded here.
    """
    FooterColumn = apps.get_model("site_details", "FooterColumn")
    FooterLink = apps.get_model("site_details", "FooterLink")

    if FooterColumn.objects.exists():
        return

    navigation = FooterColumn.objects.create(title="Navigation", order=0)
    FooterLink.objects.create(column=navigation, label="Home", url="/", order=0)
    FooterLink.objects.create(column=navigation, label="About Us", url="/about", order=1)
    FooterLink.objects.create(column=navigation, label="Premium", url="/premium", order=2)
    FooterLink.objects.create(column=navigation, label="Tests", url="/tests", order=3)

    work_process = FooterColumn.objects.create(title="Work Process", order=1)
    FooterLink.objects.create(column=work_process, label="Choose your learning method.", url="/", order=0)
    FooterLink.objects.create(column=work_process, label="Access to all tests", url="/tests", order=1)
    FooterLink.objects.create(column=work_process, label="Choose Your Package", url="/premium", order=2)
    FooterLink.objects.create(column=work_process, label="Partners", url="/", order=3)


def remove_footer_navigation(apps, schema_editor):
    """
    Remove the seeded footer columns (links cascade).
    """
    FooterColumn = apps.get_model("site_details", "FooterColumn")
    FooterColumn.objects.filter(title__in=["Navigation", "Work Process"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_details", "0049_footercolumn_footerlink"),
    ]

    operations = [
        migrations.RunPython(seed_footer_navigation, remove_footer_navigation),
    ]
