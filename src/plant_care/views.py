from tokenize import group

from django.contrib import messages
from django.db.models import QuerySet, Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.forms import PlantModelForm, PlantGroupModelForm, CauseOfDeathForm, \
    PlantTaskFrequencyGenericForm, PlantTaskGenericForm, \
    PlantAndTaskGenericUpdateForm, BasePlantAndTaskGenericForm, PlantCareHistoryFilterForm
from plant_care.models import Plant, PlantGroup, PlantGraveyard, PlantTaskFrequency, PlantCareHistory


class HomePageTemplateView(TemplateView):
    """
    View to display the home page of the app.
    """
    template_name = "home_page.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'user_name' to context.
        """
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username
        return context


class PlantListingView(ListView):
    """
    View for displaying the list of alive plants.
    """
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, filters only alive plants.
        Allows user to filter by name or group
        """
        queryset = Plant.objects.filter(is_alive=True)
        search = self.request.GET.get("start_str")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(group__group_name__icontains=search)
            )
        return queryset


class PlantGroupListingView(ListView):
    """
    View for displaying the list of plant groups.
    """
    model = PlantGroup
    context_object_name = "groups"
    template_name = "plant_group_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, counts the number of living plants in each group
        """
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
    """
    View for displaying the list of plants in a specific group.
    """
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, filters only alive plants inside a given group
        """
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)

        return Plant.objects.filter(group=group, is_alive=True)

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'group' to context.
        """
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)
        context["group"] = group

        return context


class PlantDetailView(DetailView):
    """
    View for displaying specific plant details.
    """
    model = Plant
    template_name = "plant_detail_page_template.html"
    context_object_name = "plant"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'task_frequencies' to context.
        """
        context = super().get_context_data(**kwargs)
        plant = self.get_object()

        task_frequencies = PlantTaskFrequency.objects.filter(plant=plant)
        context["task_frequencies"] = task_frequencies

        return context


class PlantGroupDetailView(DetailView):
    """
    View for displaying specific group details.
    """
    model = PlantGroup
    template_name = "plant_group_detail_page_template.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'num_plants' to context. 'num_plants' represents the number of plants in each group
        """
        context = super().get_context_data(**kwargs)
        context["num_plants"] = self.object.plants.filter(is_alive=True).count()

        return context


class PlantGroupCreateView(CreateView):
    """
    View for creating a new plant group.
    """
    model = PlantGroup
    template_name = "plant_group_create_page_template.html"
    form_class = PlantGroupModelForm

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly created plant group.
        """
        return self.object.get_absolute_url()


class PlantGroupUpdateView(UpdateView):
    """
    View for updating an existing plant group.
    """
    template_name = "plant_group_update_page_template.html"
    model = PlantGroup
    form_class = PlantGroupModelForm
    context_object_name = "group"

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly updated plant group.
        """
        return self.object.get_absolute_url()


class PlantDeleteView(DeleteView):
    """
    View for deleting an existing plant.
    """
    template_name = "plant_delete_page_templete.html"
    model = Plant
    context_object_name = "plant"

    def get_success_url(self) -> str:
        """
        Returns the URL to redirect to after successfully deleting a plant.
        When the plant is alive, redirects to plant list. If not, redirects to graveyard list.
        """
        if not self.object.is_alive:
            return reverse_lazy("plant_care:plant-graveyard-list")
        else:
            return reverse_lazy("plant_care:plant-list")


class PlantGroupDeleteView(DeleteView):
    """
    View for deleting an existing plant group.
    'Uncategorized' group cannot be deleted.
    """
    template_name = "plant_group_delete_page_templete.html"
    model = PlantGroup
    success_url = reverse_lazy("plant_care:plant-group-list")
    context_object_name = "group"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """
        Prevents the deletion of default 'Uncategorized' group in the post method. Redirects the user to plant group list.
        """
        group = self.get_object()
        if group.group_name == "Uncategorized":
            messages.warning(request, "The 'Uncategorized' group cannot be deleted!")
            return redirect('plant_care:plant-group-list')

        return super().post(request, *args, **kwargs)


class DeadPlantView(FormView):
    """
    View for marking a plant as dead (is_alive=False).
    """
    template_name = "plant_dead_page_templete.html"
    form_class = CauseOfDeathForm
    success_url = reverse_lazy("plant_care:plant-graveyard-list")

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'plant' to context.
        """
        context = super().get_context_data(**kwargs)

        plant_id = self.kwargs.get('pk')
        context["plant"] = Plant.objects.get(pk=plant_id)
        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Overrides parent method 'form_valid' to handle the process after the form is validated by user.
        If the form is validated, calls the 'move_to_graveyard' method on the plant object to mark it as dead, records the cause of death and moves it to the 'graveyard'.
        """
        plant_id = self.kwargs['pk']
        plant = get_object_or_404(Plant, pk=plant_id)
        reason = form.cleaned_data.get('cause_of_death')

        plant.move_to_graveyard(reason)

        self.plant = plant

        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly deceased plant.
        """
        return self.plant.get_absolute_url()


class PlantGraveyardListingView(ListView):
    """
    View for displaying the list of dead plants (plants in the graveyard).
    """
    model = PlantGraveyard
    template_name = "plant_graveyard_listing_page_template.html"
    context_object_name = "graveyard"


def plant_create_functional_view(request):
    """ not in use, changed to CBV"""
    if request.method == "POST":
        plant_form = PlantModelForm(request.POST)
        task_frequency_form = PlantTaskFrequencyGenericForm(request.POST)

        if plant_form.is_valid() and task_frequency_form.is_valid():
            plant = plant_form.save()
            print(task_frequency_form.cleaned_data)
            task_frequency_form.save(plant)

            return redirect("plant_care:plant-list")
    else:
        plant_form = PlantModelForm()
        task_frequency_form = PlantTaskFrequencyGenericForm()

    return render(request, "plant_create_page_forms_template.html", {
        "plant_form": plant_form,
        "task_frequency_form": task_frequency_form
    })


class PlantAndTaskFrequencyCreateGenericFormView(FormView):
    """
    View for creating a new plant and its related task frequencies.
    """
    template_name = "plant_create_page_template.html"
    form_class = BasePlantAndTaskGenericForm

    def get_form_kwargs(self) -> dict:
        """
        Overrides parent method get_form_kwargs, adds initial data for task frequencies based on TASK_FREQUENCIES.
        """
        form_kwargs = super().get_form_kwargs()

        initial_data = {}
        for task, task_display in TASK_CATEGORY_CHOICES:
            initial_data[task] = TASK_FREQUENCIES.get(task, None)

        form_kwargs["initial"] = initial_data
        return form_kwargs

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Overrides parent method 'form_valid' to handle the process after the form is validated by user.
        After validation creates a new plant object and its related task frequencies objects.
        """
        plant = Plant.objects.create(
            name=form.cleaned_data["name"],
            group=form.cleaned_data["group"],
            date=form.cleaned_data["date"],
            notes=form.cleaned_data["notes"],
        )

        for task, task_display in TASK_CATEGORY_CHOICES:
            frequency = form.cleaned_data.get(task)
            if frequency is not None:
                PlantTaskFrequency.objects.create(
                    plant=plant,
                    task_type=task,
                    frequency=frequency,
                )

        self.plant = plant  # aby sel get_succes_url

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly created plant.
        """
        return self.plant.get_absolute_url()


class PlantAndTaskFrequencyUpdateGenericFormView(FormView):
    """
    View for updating a plant and its related task frequencies.
    """
    template_name = "plant_update_page_template.html"
    form_class = PlantAndTaskGenericUpdateForm

    def get_form_kwargs(self) -> dict:
        """
        Overrides parent method get_form_kwargs, adds initial data for the plant and its task frequencies.
        """
        form_kwargs = super().get_form_kwargs()
        plant_id = self.kwargs.get("pk")
        plant = get_object_or_404(Plant, pk=plant_id)
        form_kwargs["plant"] = plant

        initial_data = {
            "name": plant.name,
            "group": plant.group,
            "date": plant.date,
            "notes": plant.notes,
        }

        for task, task_display in TASK_CATEGORY_CHOICES:
            existing_value = plant.task_frequencies.filter(task_type=task).first()
            if existing_value:
                initial_data[task] = existing_value.frequency
            else:
                initial_data[task] = TASK_FREQUENCIES.get(task)

        form_kwargs["initial"] = initial_data
        return form_kwargs

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Overrides parent method 'form_valid' to handle the form submisson and update the plant
        and task frequency objects.
        """
        plant = form.plant
        plant.name = form.cleaned_data["name"]
        plant.group = form.cleaned_data["group"]
        plant.date = form.cleaned_data["date"]
        plant.notes = form.cleaned_data["notes"]
        plant.save()

        for task, task_display in TASK_CATEGORY_CHOICES:
            frequency = form.cleaned_data.get(task)
            task_existing = plant.task_frequencies.filter(task_type=task).first()

            if frequency is not None:
                if task_existing:
                    task_existing.frequency = frequency
                    task_existing.save()
                else:
                    # if task frequency was not previously set, but it was added during update
                    PlantTaskFrequency.objects.create(plant=plant, task_type=task, frequency=frequency)
            elif task_existing:
                # if field is left empty, set to default
                default_frequency = TASK_FREQUENCIES.get(task, None)
                task_existing.frequency = default_frequency
                task_existing.save()

        self.plant = plant

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly updated plant.
        """
        return self.plant.get_absolute_url()


class PerformTaskView(FormView):
    """
    View for performing a task. User can select one or more plants and perform a specific task.
    Creates a PlantCareHistory object.
    """
    template_name = "plant_perform_tasks_list_page_template.html"
    form_class = PlantTaskGenericForm
    success_url = reverse_lazy("plant_care:care-history")

    def get_context_data(self, **kwargs):
        """"""
        context = super().get_context_data(**kwargs)
        context["plants"] = Plant.objects.filter(is_alive=True)
        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """"""
        task_types = form.cleaned_data["task_type"]
        plant_list = form.cleaned_data["plants"]
        print(f"Task Type: {task_types}")
        print(f"Selected Plants: {plant_list}")

        for plant in plant_list:
            for task_type in task_types:
                PlantCareHistory.objects.create(
                    plant=plant,
                    task_type=task_type,
                    task_date=now()
                )
        return super().form_valid(form)


class PlantCareHistoryListingView(ListView):
    """"""
    model = PlantCareHistory
    template_name = "plant_care_history_listing_page_template.html"
    context_object_name = "history"

    def get_queryset(self):
        # https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related

        queryset = PlantCareHistory.objects.select_related('plant').order_by("-task_date").all()
        search = self.request.GET.get("start_str")
        if search:
            queryset = queryset.filter(
                Q(task_type__icontains=search) |
                Q(plant__group__group_name__istartswith=search) |
                Q(plant__name__istartswith=search)
            )
        return queryset


class PlantCareHistoryDeleteView(DeleteView):
    """
    View for deleting a plant care history log.
    """
    model = PlantCareHistory
    success_url = reverse_lazy("plant_care:care-history")
    template_name = "plant_care_history_delete_page_template.html"
    context_object_name = "history"
