from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, RegisterView, ConfirmEmailView, ResetPasswordView, 
    RequestPasswordResetView, GoogleLoginView
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("email/confirm/", ConfirmEmailView.as_view(), name="email-confirm"),
    path("password/forgot/", RequestPasswordResetView.as_view(), name="password-forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
]