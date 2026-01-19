from django.db import models
from django.conf import settings

class State(models.Model):
    name = models.CharField(max_length=80, unique=True)
    
    # Multilingual fields - Russian
    name_ru = models.CharField(max_length=80, blank=True, verbose_name="Name (Russian)")
    
    # Multilingual fields - Armenian
    name_hy = models.CharField(max_length=80, blank=True, verbose_name="Name (Armenian)")
    
    # Multilingual fields - Hindi
    name_hi = models.CharField(max_length=80, blank=True, verbose_name="Name (Hindi)")
    
    # Multilingual fields - Spanish
    name_es = models.CharField(max_length=80, blank=True, verbose_name="Name (Spanish)")
    
    # Multilingual fields - Chinese
    name_zh = models.CharField(max_length=80, blank=True, verbose_name="Name (Chinese)")
    
    def __str__(self):
        return self.name

class Vehicle(models.Model):
    name = models.CharField(max_length=80, unique=True)
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True, help_text="Upload vehicle type icon")
    image_width = models.PositiveIntegerField(null=True, blank=True, help_text="Image width in pixels")
    image_height = models.PositiveIntegerField(null=True, blank=True, help_text="Image height in pixels")
    
    # Multilingual fields - Russian
    name_ru = models.CharField(max_length=80, blank=True, verbose_name="Name (Russian)")
    
    # Multilingual fields - Armenian
    name_hy = models.CharField(max_length=80, blank=True, verbose_name="Name (Armenian)")
    
    # Multilingual fields - Hindi
    name_hi = models.CharField(max_length=80, blank=True, verbose_name="Name (Hindi)")
    
    # Multilingual fields - Spanish
    name_es = models.CharField(max_length=80, blank=True, verbose_name="Name (Spanish)")
    
    # Multilingual fields - Chinese
    name_zh = models.CharField(max_length=80, blank=True, verbose_name="Name (Chinese)")
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.email}"
