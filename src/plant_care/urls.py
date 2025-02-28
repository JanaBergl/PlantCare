from django.urls import path

from plant_care.views import HomePageTemplateView

app_name = 'plant_care'

urlpatterns = [
    path('', HomePageTemplateView.as_view(), name='home-page-app'),
]
