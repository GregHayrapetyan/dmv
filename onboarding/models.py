from django.db import models
from django.conf import settings

class State(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self):
        return self.name

class Profile(models.Model):
    class Vehicle(models.TextChoices):
        CAR = "car", "Car"
        MOTO = "motorcycle", "Motorcycle"
        CDL = "cdl", "CDL"

    class Knowledge(models.TextChoices):
        VERY_WELL = "very_well", "I know them very well"
        SOME_DETAILS = "some_details", "I know them but forgot some details"
        AVERAGE = "average", "I know them at an average level"
        BARELY = "barely", "I barely know them"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    vehicle = models.CharField(max_length=20, choices=Vehicle.choices, null=True, blank=True)
    knowledge = models.CharField(max_length=20, choices=Knowledge.choices, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.email}"
