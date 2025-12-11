from django.contrib import admin
from .models import State, Vehicle, Knowledge, Profile


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'state', 'vehicle', 'knowledge', 'age', 'gender')
    list_filter = ('vehicle', 'knowledge', 'state', 'gender')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)