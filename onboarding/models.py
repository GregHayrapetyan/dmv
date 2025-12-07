from django.db import models
from django.conf import settings

class State(models.Model):
    name = models.CharField(max_length=80, unique=True)
    
    def __str__(self):
        return self.name

class Vehicle(models.Model):
    name = models.CharField(max_length=80, unique=True)
    
    def __str__(self):
        return self.name

class Knowledge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)
    knowledge = models.ForeignKey(Knowledge, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Profile for {self.user.email}"
