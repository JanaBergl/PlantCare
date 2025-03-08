from django.contrib import admin
from plant_care.models import Plant, PlantGroup, PlantTaskFrequency, PlantCareHistory, PlantGraveyard

admin.site.register(Plant)
admin.site.register(PlantGroup)
admin.site.register(PlantTaskFrequency)
admin.site.register(PlantCareHistory)
admin.site.register(PlantGraveyard)