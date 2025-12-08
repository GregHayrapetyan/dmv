from django.shortcuts import render

from django.views.generic import ListView
from .models import Plan


class PricingView(ListView):
    """
    Public pricing page view.
    Renders active plans with their features.
    """
    model = Plan
    template_name = "pricing/pricing_page.html"
    context_object_name = "plans"

    def get_queryset(self):
        """
        Only show active plans on the public page.
        """
        return Plan.objects.filter(is_active=True)

