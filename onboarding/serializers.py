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
    state_name = serializers.CharField(source='state.name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    knowledge_name = serializers.CharField(source='knowledge.name', read_only=True)
    
    class Meta:
        model = Profile
        fields = ("state", "state_name", "vehicle", "vehicle_name", "knowledge", "knowledge_name", "age", "gender")