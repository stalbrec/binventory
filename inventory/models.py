from django.db import models
from django.urls import reverse

# Create your models here.


class Box(models.Model):
    name = models.CharField(max_length=20)
    location = models.CharField(max_length=50)

    def get_absolute_url(self):
        return reverse("inventory:box", kwargs=dict(pk=self.pk))
    
    def __str__(self):
        return f"{self.name} ({self.location})"


class Item(models.Model):
    name = models.CharField(max_length=200)
    box = models.ForeignKey(Box, on_delete=models.CASCADE)

    def location(self):
        return self.box.location
    
    def __str__(self):
        return f"{self.name}"
