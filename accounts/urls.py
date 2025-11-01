from django.urls import path
from .views import (
    LoginView
)
from drf_spectacular.utils import extend_schema

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
]