from django.contrib import admin
from .models import ElevatorSystem, ElevatorRequest, ElevatorStation

# Register your models here.
admin.site.register(ElevatorSystem)
admin.site.register(ElevatorRequest)
admin.site.register(ElevatorStation)
