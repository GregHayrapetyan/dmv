from django.urls import path
from .views import (
    LoginView, RegisterView, ConfirmEmailView, ResetPasswordView, RequestPasswordResetView
)
from drf_spectacular.utils import extend_schema
from accounts.views import GoogleLoginView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("email/confirm/", ConfirmEmailView.as_view(), name="email-confirm"),
    path("password/forgot/", RequestPasswordResetView.as_view(), name="password-forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),

]