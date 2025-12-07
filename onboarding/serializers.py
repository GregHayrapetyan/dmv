from rest_framework import serializers
from .models import State, Vehicle, Knowledge, Profile

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ("id", "name")

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ("id", "name")

class KnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Knowledge
        fields = ("id", "name")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("state", "vehicle", "knowledge")