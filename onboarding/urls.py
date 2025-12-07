from django.urls import path
from .views import StateListView, VehicleListView, KnowledgeListView, ProfileRetrieveUpdateView

urlpatterns = [
    path("states/", StateListView.as_view(), name="states"),
    path("vehicles/", VehicleListView.as_view(), name="vehicles"),
    path("knowledge/", KnowledgeListView.as_view(), name="knowledge"),
    path("profile/", ProfileRetrieveUpdateView.as_view(), name="profile"),
]
