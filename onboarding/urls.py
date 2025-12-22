from django.urls import path
from .views import StateListView, VehicleListView, ProfileRetrieveUpdateView

urlpatterns = [
    path("states/", StateListView.as_view(), name="states"),
    path("vehicles/", VehicleListView.as_view(), name="vehicles"),
    path("profile/", ProfileRetrieveUpdateView.as_view(), name="profile"),
]
