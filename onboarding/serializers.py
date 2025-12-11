from rest_framework import serializers
from .models import State, Vehicle, Knowledge, Profile

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ("id", "name")

class VehicleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='name', read_only=True)
    image = serializers.SerializerMethodField()
    imageSize = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = ("id", "label", "image", "imageSize")
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_imageSize(self, obj):
        if obj.image_width and obj.image_height:
            return {
                "width": obj.image_width,
                "height": obj.image_height
            }
        return None

class KnowledgeSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='name', read_only=True)
    image = serializers.SerializerMethodField()
    imageSize = serializers.SerializerMethodField()
    
    class Meta:
        model = Knowledge
        fields = ("id", "label", "image", "imageSize")
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_imageSize(self, obj):
        if obj.image_width and obj.image_height:
            return {
                "width": obj.image_width,
                "height": obj.image_height
            }
        return None

class ProfileSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    knowledge_name = serializers.CharField(source='knowledge.name', read_only=True)
    
    class Meta:
        model = Profile
        fields = ("state", "state_name", "vehicle", "vehicle_name", "knowledge", "knowledge_name", "age", "gender")