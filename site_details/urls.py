from django.urls import path
from .views import ClientReviewListAPIView, PricingPlanListAPIView

urlpatterns = [
    path("reviews/", ClientReviewListAPIView.as_view(), name="client-reviews-list"),
    path("pricing-plans/", PricingPlanListAPIView.as_view(), name="pricing-plans-list"),
]
