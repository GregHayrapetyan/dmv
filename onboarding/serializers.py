from rest_framework import serializers
from .models import State, Vehicle, Profile
from dmv.translation import TranslatedSerializerMixin

class StateSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for State model.
    Returns state with name. Supports translations via ?lang= query parameter.
    """
    translated_fields = ['name']
    
    class Meta:
        model = State
        fields = ("id", "name")

class VehicleSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for Vehicle model.
    Returns vehicle with label, image, and imageSize.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['name']
    label = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    imageSize = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = ("id", "label", "image", "imageSize")
    
    def get_label(self, obj):
        """
        Return translated name as label.
        """
        from dmv.translation import get_translated_value
        lang = self.get_language()
        return get_translated_value(obj, 'name', lang)
    
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
    
    class Meta:
        model = Profile
        fields = ("state", "state_name", "vehicle", "vehicle_name", "age", "gender")