from django.urls import path
from plant_care.views import HomePageTemplateView, PlantListingView, PlantDetailView, PlantCreateView, \
    PlantGroupCreateView, PlantGroupListingView, PlantGroupDetailView, PlantUpdateView, PlantGroupUpdateView, \
    PlantDeleteView, PlantGroupDeleteView, DeadPlantView, PlantGraveyardListingView, PlantsInGroupListingView, \
    plant_create_functional_view, PlantAndTaskFrequencyCreateGenericFormView, PlantAndTaskFrequencyUpdateGenericFormView

app_name = 'plant_care'

urlpatterns = [
    path('', HomePageTemplateView.as_view(), name='home-page-app'),
    path('list/', PlantListingView.as_view(), name='plant-list'),
    path('group-list/', PlantGroupListingView.as_view(), name='plant-group-list'),
    path('plants-in-group-list/<int:pk>', PlantsInGroupListingView.as_view(), name='plants-in-group-list'),
    path('detail/<int:pk>/', PlantDetailView.as_view(), name='plant-detail'),
    path('group-detail/<int:pk>/', PlantGroupDetailView.as_view(), name='plant-group-detail'),
    path('create-plant/', PlantAndTaskFrequencyCreateGenericFormView.as_view(), name='plant-create'),
    path('create-group/', PlantGroupCreateView.as_view(), name='plant-group-create'),
    path('update/<int:pk>/', PlantAndTaskFrequencyUpdateGenericFormView.as_view(), name='plant-update'),
    path('update-group/<int:pk>/', PlantGroupUpdateView.as_view(), name='plant-group-update'),
    path('delete/<int:pk>/', PlantDeleteView.as_view(), name='plant-delete'),
    path('delete-group/<int:pk>/', PlantGroupDeleteView.as_view(), name='plant-group-delete'),
    path('dead/<int:pk>/', DeadPlantView.as_view(), name='dead-plant'),
    path('graveyard-list/', PlantGraveyardListingView.as_view(), name='plant-graveyard-list'),
    #path('create-form/', plant_create_functional_view, name='plant_create-form'),
    #path('create-view/', PlantAndTaskFrequencyCreateView.as_view(), name='plant_create-view'),
    #path('update-view/<int:pk>/', PlantAndTaskFrequencyUpdateView.as_view(), name='plant_update-view'),
]
