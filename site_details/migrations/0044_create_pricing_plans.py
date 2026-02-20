# Generated migration for creating 3 pricing plans

from django.db import migrations


def create_pricing_plans(apps, schema_editor):
    """Create the 3 pricing plans: Starter, Standard, and Premium."""
    PricingPlan = apps.get_model('site_details', 'PricingPlan')
    PlanFeature = apps.get_model('site_details', 'PlanFeature')
    
    # Clear existing plans if any
    PricingPlan.objects.all().delete()
    
    # Plan 1: Starter - 7 Days Access ($9.99)
    starter = PricingPlan.objects.create(
        subtitle="7-DAY ACCESS",
        title="Starter",
        description="Perfect for focused, short-term preparation before your DMV test.",
        price_old=None,
        price_period="/7 days",
        price_new=9.99,
        discount_amount=0,
        button_text="Get Started",
        button_url="/checkout/starter",
        is_featured=False,
        order=0,
        is_active=True,
        stripe_price_id_monthly="",  # Add your Stripe recurring Price ID here (7-day interval)
    )
    
    # Starter features
    PlanFeature.objects.create(
        plan=starter,
        text="7 days full access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=0
    )
    PlanFeature.objects.create(
        plan=starter,
        text="All 650+ exam-like questions",
        is_included=True,
        icon_type="pricing_icons/book.svg",
        order=1
    )
    PlanFeature.objects.create(
        plan=starter,
        text="Practice tests and simulations",
        is_included=True,
        icon_type="pricing_icons/simulation.svg",
        order=2
    )
    PlanFeature.objects.create(
        plan=starter,
        text="Mobile access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=3
    )
    
    # Plan 2: Standard - 30 Days Access ($19.99) - MOST POPULAR
    standard = PricingPlan.objects.create(
        subtitle="MOST POPULAR",
        title="Standard",
        description="30 days of comprehensive study time to master your DMV test.",
        price_old=None,
        price_period="/30 days",
        price_new=19.99,
        discount_amount=0,
        button_text="Get Started",
        button_url="/checkout/standard",
        is_featured=True,
        order=1,
        is_active=True,
        stripe_price_id_monthly="",  # Add your Stripe recurring Price ID here (30-day interval)
    )
    
    # Standard features
    PlanFeature.objects.create(
        plan=standard,
        text="30 days full access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=0
    )
    PlanFeature.objects.create(
        plan=standard,
        text="All 650+ exam-like questions",
        is_included=True,
        icon_type="pricing_icons/book.svg",
        order=1
    )
    PlanFeature.objects.create(
        plan=standard,
        text="Practice tests and simulations",
        is_included=True,
        icon_type="pricing_icons/simulation.svg",
        order=2
    )
    PlanFeature.objects.create(
        plan=standard,
        text="Behind-the-wheel simulators",
        is_included=True,
        icon_type="pricing_icons/shield.svg",
        order=3
    )
    PlanFeature.objects.create(
        plan=standard,
        text="Progress tracking",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=4
    )
    PlanFeature.objects.create(
        plan=standard,
        text="Mobile access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=5
    )
    
    # Plan 3: Premium - 90 Days Access ($29.99)
    premium = PricingPlan.objects.create(
        subtitle="BEST VALUE",
        title="Premium",
        description="90 days of unlimited access for thorough preparation and confidence.",
        price_old=None,
        price_period="/90 days",
        price_new=29.99,
        discount_amount=0,
        button_text="Get Started",
        button_url="/checkout/premium",
        is_featured=False,
        order=2,
        is_active=True,
        stripe_price_id_monthly="",  # Add your Stripe recurring Price ID here (90-day interval)
    )
    
    # Premium features
    PlanFeature.objects.create(
        plan=premium,
        text="90 days full access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=0
    )
    PlanFeature.objects.create(
        plan=premium,
        text="All 650+ exam-like questions",
        is_included=True,
        icon_type="pricing_icons/book.svg",
        order=1
    )
    PlanFeature.objects.create(
        plan=premium,
        text="Practice tests and simulations",
        is_included=True,
        icon_type="pricing_icons/simulation.svg",
        order=2
    )
    PlanFeature.objects.create(
        plan=premium,
        text="Behind-the-wheel simulators",
        is_included=True,
        icon_type="pricing_icons/shield.svg",
        order=3
    )
    PlanFeature.objects.create(
        plan=premium,
        text="Progress tracking & analytics",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=4
    )
    PlanFeature.objects.create(
        plan=premium,
        text="Priority email support",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=5
    )
    PlanFeature.objects.create(
        plan=premium,
        text="Mobile access",
        is_included=True,
        icon_type="pricing_icons/check.svg",
        order=6
    )


def reverse_pricing_plans(apps, schema_editor):
    """Remove the created pricing plans."""
    PricingPlan = apps.get_model('site_details', 'PricingPlan')
    PricingPlan.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('site_details', '0043_add_multilingual_fields_to_clientreview'),
    ]

    operations = [
        migrations.RunPython(create_pricing_plans, reverse_pricing_plans),
    ]
