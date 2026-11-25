"""Minimal URLConf for subscription status/detail API tests."""
from django.urls import path

from accounts.subscription_views import SubscriptionDetailView, SubscriptionStatusView

urlpatterns = [
    path('api/accounts/subscription/detail/', SubscriptionDetailView.as_view()),
    path('api/accounts/subscription/status/', SubscriptionStatusView.as_view()),
]
