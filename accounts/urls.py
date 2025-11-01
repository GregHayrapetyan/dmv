from django.urls import path
from .views import (
    LoginView, RegisterView, ConfirmEmailView
)
from drf_spectacular.utils import extend_schema

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("email/confirm/", ConfirmEmailView.as_view(), name="email-confirm"),
]