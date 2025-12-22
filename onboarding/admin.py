from django.contrib import admin
from .models import State, Vehicle, Profile


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image', 'image_width', 'image_height')
    search_fields = ('name',)
    fields = ('name', 'image', 'image_width', 'image_height')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'state', 'vehicle', 'age', 'gender')
    list_filter = ('vehicle', 'state', 'gender')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)