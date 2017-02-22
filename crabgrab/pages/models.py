from django.db import models

# Create your models here.


class Locations(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    latitude = models.CharField(max_length=255)
    longitude = models.CharField(max_length=255)
    prediction_type = models.CharField(max_length=255)


class Tides(models.Model):
    location = models.ForeignKey("Locations")
    datetime = models.DateTimeField()
    height = models.CharField(max_length=10)
    H_L = models.CharField(max_length=10)
    classification = models.CharField(max_length=25)
    change = models.CharField(max_length=10)
