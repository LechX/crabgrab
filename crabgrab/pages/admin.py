from django.contrib import admin
from .models import Tides, Locations

# Register your models here.
admin.site.register(Tides)
admin.site.register(Locations)
