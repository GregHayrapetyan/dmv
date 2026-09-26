from django.urls import path
from .views import (
    LoginView, RegisterView, ConfirmEmailView, ResetPasswordView, 
    RequestPasswordResetView, GoogleLoginView, AppleLoginView, MeView, CookieTokenRefreshView, LogoutView,
    SetAvatarView, DeleteAccountView, ChangePasswordView
)
from .subscription_views import (
    CreateCheckoutSessionView, CreateBillingPortalSessionView,
    SubscriptionStatusView, CancelSubscriptionView, StripeWebhookView,
    SubscriptionDetailView, ReactivateSubscriptionView, ChangePlanView,
    UpdatePaymentMethodView, UpdateBillingInfoView
)
from .apple_iap_views import (
    AppleVerifyPurchaseView, AppleServerNotificationView
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    path("email/confirm/", ConfirmEmailView.as_view(), name="email-confirm"),
    path("password/forgot/", RequestPasswordResetView.as_view(), name="password-forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("apple/", AppleLoginView.as_view(), name="apple-login"),
    path("me/", MeView.as_view(), name="me"),
    path("set_avatar/", SetAvatarView.as_view(), name="set-avatar"),
    path("delete_account/", DeleteAccountView.as_view(), name="delete-account"),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
    
    # Subscription endpoints
    path("subscription/checkout/", CreateCheckoutSessionView.as_view(), name="subscription-checkout"),
    path("subscription/portal/", CreateBillingPortalSessionView.as_view(), name="subscription-portal"),
    path("subscription/status/", SubscriptionStatusView.as_view(), name="subscription-status"),
    path("subscription/detail/", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("subscription/cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("subscription/reactivate/", ReactivateSubscriptionView.as_view(), name="subscription-reactivate"),
    path("subscription/change-plan/", ChangePlanView.as_view(), name="subscription-change-plan"),
    path("subscription/update-payment/", UpdatePaymentMethodView.as_view(), name="subscription-update-payment"),
    path("subscription/update-billing/", UpdateBillingInfoView.as_view(), name="subscription-update-billing"),
    path("subscription/webhook/", StripeWebhookView.as_view(), name="subscription-webhook"),

    # Apple In-App Purchase (iOS) endpoints
    path("subscription/apple/verify/", AppleVerifyPurchaseView.as_view(), name="subscription-apple-verify"),
    path("subscription/apple/notifications/", AppleServerNotificationView.as_view(), name="subscription-apple-notifications"),
]