from django.urls import path
from plant_care.views import HomePageTemplateView, PlantListingView, PlantDetailView, PlantCreateView, \
    PlantGroupCreateView, PlantGroupListingView, PlantGroupDetailView, PlantUpdateView, PlantGroupUpdateView, \
    PlantDeleteView, PlantGroupDeleteView

app_name = 'plant_care'

urlpatterns = [
    path('', HomePageTemplateView.as_view(), name='home-page-app'),
    path('list/', PlantListingView.as_view(), name='plant-list'),
    path('group-list/', PlantGroupListingView.as_view(), name='plant-group-list'),
    path('detail/<int:pk>/', PlantDetailView.as_view(), name='plant-detail'),
    path('group-detail/<int:pk>/', PlantGroupDetailView.as_view(), name='plant-group-detail'),
    path('create-plant/', PlantCreateView.as_view(), name='plant-create'),
    path('create-group/', PlantGroupCreateView.as_view(), name='plant-group-create'),
    path('update/<int:pk>/', PlantUpdateView.as_view(), name='plant-update'),
    path('update-group/<int:pk>/', PlantGroupUpdateView.as_view(), name='plant-group-update'),
    path('delete/<int:pk>/', PlantDeleteView.as_view(), name='plant-delete'),
    path('delete-group/<int:pk>/', PlantGroupDeleteView.as_view(), name='plant-group-delete'),

]
