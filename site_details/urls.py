from django.urls import path
from .views import (
    ClientReviewListAPIView,
    PricingPlanListAPIView,
    ContactCreateAPIView,
    ContactInfoRetrieveAPIView,
    PartnerListAPIView,
    MainBannerRetrieveAPIView,
    HowItWorksRetrieveAPIView,
    TrustSafetyRetrieveAPIView,
    SuccessStepsRetrieveAPIView,
    LearningOptionsRetrieveAPIView,
    SocialNetworkListAPIView,
)

urlpatterns = [
    path("reviews/", ClientReviewListAPIView.as_view(), name="client-reviews-list"),
    path("pricing-plans/", PricingPlanListAPIView.as_view(), name="pricing-plans-list"),
    path("contact/", ContactCreateAPIView.as_view(), name="contact-create"),
    path("contact-info/", ContactInfoRetrieveAPIView.as_view(), name="contact-info"),
    path("partners/", PartnerListAPIView.as_view(), name="partners-list"),
    path("main-banner/", MainBannerRetrieveAPIView.as_view(), name="main-banner"),
    path("how-it-works/", HowItWorksRetrieveAPIView.as_view(), name="how-it-works"),
    path("trust-safety/", TrustSafetyRetrieveAPIView.as_view(), name="trust-safety"),
    path("success-steps/", SuccessStepsRetrieveAPIView.as_view(), name="success-steps"),
    path("learning-options/", LearningOptionsRetrieveAPIView.as_view(), name="learning-options"),
    path("social-networks/", SocialNetworkListAPIView.as_view(), name="social-networks-list"),
]
