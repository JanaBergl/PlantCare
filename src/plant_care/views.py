from django.contrib import messages
from django.db.models import QuerySet, Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from plant_care.forms import PlantModelForm, PlantGroupModelForm, CauseOfDeathForm
from plant_care.models import Plant, PlantGroup, PlantGraveyard

"""
Listování rostlin: Zobrazit všechny rostliny v databázi - různé řazení - datum, jméno, skupiny.
Detail rostliny: Detailní zobrazení jedné rostliny a její péče (zálivka, hnojení, atd.).
Přidání nové rostliny: Formulář pro přidání nové rostliny.
Úprava rostliny: Formulář pro úpravu existující rostliny.
Zobrazení varování
Seznam mrtvých rostlin
Zalévání, ...

"""


class HomePageTemplateView(TemplateView):
    """"""
    template_name = "home_page.html"

    def get_context_data(self, **kwargs) -> dict:
        """Overrides parent method get_context_data, adds 'user_name' to context."""
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username
        return context


class PlantListingView(ListView):
    """"""
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """Overrides parent method get_queryset, filters only alive plants"""
        return Plant.objects.filter(is_alive=True)


class PlantGroupListingView(ListView):
    """"""
    model = PlantGroup
    context_object_name = "groups"
    template_name = "plant_group_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """Overrides parent method get_queryset, counts the number of living plants in each group"""
        return PlantGroup.objects.annotate(
            num_plants=Count("plants", filter=Q(plants__is_alive=True))
        )

    """ moznost 2
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for group in context["groups"]:
            group.num_plants = group.plants.filter(is_alive=True).count()
        return context
    """
class PlantsInGroupListingView(ListView):
    """"""
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """Overrides parent method get_queryset, filters only alive plants inside a given group"""
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)

        return Plant.objects.filter(group=group, is_alive=True)

    def get_context_data(self, **kwargs) -> dict:
        """Overrides parent method get_context_data, adds 'group' to context."""
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)
        context["group"] = group

        return context


class PlantDetailView(DetailView):
    """"""
    model = Plant
    template_name = "plant_detail_page_template.html"
    context_object_name = "plant"


class PlantGroupDetailView(DetailView):
    """"""
    model = PlantGroup
    template_name = "plant_group_detail_page_template.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs) -> dict:
        """Overrides parent method get_context_data, adds 'num_plants' to context. 'num_plants' represents the number of plants in each group"""
        context = super().get_context_data(**kwargs)
        context["num_plants"] = self.object.plants.filter(is_alive=True).count()

        return context


class PlantCreateView(CreateView):
    """"""
    model = Plant
    template_name = "plant_create_page_template.html"
    form_class = PlantModelForm
    success_url = reverse_lazy("plant_care:plant-list")


class PlantGroupCreateView(CreateView):
    """"""
    model = PlantGroup
    template_name = "plant_group_create_page_template.html"
    form_class = PlantGroupModelForm
    success_url = reverse_lazy("plant_care:plant-group-list")


class PlantUpdateView(UpdateView):
    """"""
    template_name = "plant_update_page_template.html"
    model = Plant
    form_class = PlantModelForm
    success_url = reverse_lazy("plant_care:plant-list")
    context_object_name = "plant"


class PlantGroupUpdateView(UpdateView):
    """"""
    template_name = "plant_group_update_page_template.html"
    model = PlantGroup
    form_class = PlantGroupModelForm
    success_url = reverse_lazy("plant_care:plant-group-list")
    context_object_name = "group"


class PlantDeleteView(DeleteView):
    """"""
    template_name = "plant_delete_page_templete.html"
    model = Plant
    success_url = reverse_lazy("plant_care:plant-list")
    context_object_name = "plant"


class PlantGroupDeleteView(DeleteView):
    """"""
    template_name = "plant_group_delete_page_templete.html"
    model = PlantGroup
    success_url = reverse_lazy("plant_care:plant-group-list")
    context_object_name = "group"

    def post(self, request, *args, **kwargs):
        """Prevents the deletion of default 'Uncategorized' group in the post method. Redirects the user to plant group list."""
        group = self.get_object()
        if group.group_name == "Uncategorized":
            messages.warning(request, "The 'Uncategorized' group cannot be deleted!")
            return redirect('plant_care:plant-group-list')

        # Allows deletion of other groups
        return super().post(request, *args, **kwargs)


class DeadPlantView(FormView):
    """"""
    template_name = "plant_dead_page_templete.html"
    form_class = CauseOfDeathForm
    success_url = reverse_lazy("plant_care:plant-graveyard-list")

    def get_context_data(self, **kwargs) -> dict:
        """Overrides parent method 'get_context_data', adds 'plant' to context."""
        context = super().get_context_data(**kwargs)

        plant_id = self.kwargs.get('pk')
        context["plant"] = Plant.objects.get(pk=plant_id)
        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Overrides parent method 'form_valid' to handle the process after the form is validated by user.
        If the form is validated, calls the 'move_to_graveyard' method on the plant object to mark it as dead, records the cause of death and moves it to the graveyard.
        """
        plant_id = self.kwargs['pk']
        plant = get_object_or_404(Plant, pk=plant_id)
        reason = form.cleaned_data.get('cause_of_death')

        plant.move_to_graveyard(reason)
        return redirect(self.success_url)


class PlantGraveyardListingView(ListView):
    """"""
    model = PlantGraveyard
    template_name = "plant_graveyard_listing_page_template.html"
    context_object_name = "graveyard"
