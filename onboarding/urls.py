from django.urls import path
from .views import StateListView, ProfileRetrieveUpdateView

urlpatterns = [
    path("states/", StateListView.as_view(), name="states"),
    path("profile/", ProfileRetrieveUpdateView.as_view(), name="profile"),
]
