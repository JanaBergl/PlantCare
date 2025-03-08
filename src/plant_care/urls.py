from django.urls import path
from plant_care.views import HomePageTemplateView, PlantListingView, PlantDetailView, \
    PlantGroupCreateView, PlantGroupListingView, PlantGroupDetailView, PlantGroupUpdateView, \
    PlantDeleteView, PlantGroupDeleteView, DeadPlantView, PlantGraveyardListingView, PlantsInGroupListingView, \
    PlantAndTaskFrequencyCreateGenericFormView, \
    PlantAndTaskFrequencyUpdateGenericFormView, PerformTaskView, PlantCareHistoryListingView, \
    PlantCareHistoryDeleteView, Error404PageTemplateView, PlantCareOverdueWarningsView, PlantCareHistoryUpdateView

app_name = 'plant_care'

urlpatterns = [
    # HOME PAGE
    path('', HomePageTemplateView.as_view(), name='home-page-app'),

    # LISTING VIEWS
    path('list/', PlantListingView.as_view(), name='plant-list'),
    path('list/<str:filter>/', PlantListingView.as_view(), name='plant-list-search'),
    path('group-list/', PlantGroupListingView.as_view(), name='plant-group-list'),
    path('plants-in-group-list/<int:pk>', PlantsInGroupListingView.as_view(), name='plants-in-group-list'),
    path('care-history/', PlantCareHistoryListingView.as_view(), name='care-history'),

    # DETAIL VIEWS
    path('plant-detail/<int:pk>/', PlantDetailView.as_view(), name='plant-detail'),
    path('group-detail/<int:pk>/', PlantGroupDetailView.as_view(), name='plant-group-detail'),

    # CREATE VIEWS
    path('create-plant/', PlantAndTaskFrequencyCreateGenericFormView.as_view(), name='plant-create'),
    path('create-group/', PlantGroupCreateView.as_view(), name='plant-group-create'),

    # UPDATE VIEWS
    path('update-plant/<int:pk>/', PlantAndTaskFrequencyUpdateGenericFormView.as_view(), name='plant-update'),
    path('update-group/<int:pk>/', PlantGroupUpdateView.as_view(), name='plant-group-update'),
    path('update-care-history/<int:pk>/', PlantCareHistoryUpdateView.as_view(), name='care-history-update'),

    # DELETE VIEWS
    path('delete/<int:pk>/', PlantDeleteView.as_view(), name='plant-delete'),
    path('delete-group/<int:pk>/', PlantGroupDeleteView.as_view(), name='plant-group-delete'),
    path('delete-care-history/<int:pk>/', PlantCareHistoryDeleteView.as_view(), name='care-history-delete'),

    # CUSTOM VIEWS
    path('dead/<int:pk>/', DeadPlantView.as_view(), name='dead-plant'),
    path('graveyard-list/', PlantGraveyardListingView.as_view(), name='plant-graveyard-list'),
    path('perform-tasks/', PerformTaskView.as_view(), name='perform-tasks'),
    path('warnings/', PlantCareOverdueWarningsView.as_view(), name='warnings'),

    path('zkouska/', Error404PageTemplateView.as_view(), name='error-zkouska'),

]
