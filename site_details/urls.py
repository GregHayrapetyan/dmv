from django.urls import path
from .views import (
    ClientReviewListAPIView,
    PricingPlanListAPIView,
    ContactCreateAPIView,
    ContactInfoRetrieveAPIView,
    PartnerListAPIView,
    MainBannerListAPIView,
)

urlpatterns = [
    path("reviews/", ClientReviewListAPIView.as_view(), name="client-reviews-list"),
    path("pricing-plans/", PricingPlanListAPIView.as_view(), name="pricing-plans-list"),
    path("contact/", ContactCreateAPIView.as_view(), name="contact-create"),
    path("contact-info/", ContactInfoRetrieveAPIView.as_view(), name="contact-info"),
    path("partners/", PartnerListAPIView.as_view(), name="partners-list"),
    path("main-banner/", MainBannerListAPIView.as_view(), name="main-banner-list"),
]
