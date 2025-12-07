from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, RegisterView, ConfirmEmailView, ResetPasswordView, 
    RequestPasswordResetView, GoogleLoginView, MeView
)
from .subscription_views import (
    CreateCheckoutSessionView, CreateBillingPortalSessionView,
    SubscriptionStatusView, CancelSubscriptionView, StripeWebhookView
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("email/confirm/", ConfirmEmailView.as_view(), name="email-confirm"),
    path("password/forgot/", RequestPasswordResetView.as_view(), name="password-forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("me/", MeView.as_view(), name="me"),
    
    # Subscription endpoints
    path("subscription/checkout/", CreateCheckoutSessionView.as_view(), name="subscription-checkout"),
    path("subscription/portal/", CreateBillingPortalSessionView.as_view(), name="subscription-portal"),
    path("subscription/status/", SubscriptionStatusView.as_view(), name="subscription-status"),
    path("subscription/cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("subscription/webhook/", StripeWebhookView.as_view(), name="subscription-webhook"),
]