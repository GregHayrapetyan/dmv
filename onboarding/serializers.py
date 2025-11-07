from rest_framework import serializers
from .models import State, Profile

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ("id", "name")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("state", "vehicle", "knowledge")