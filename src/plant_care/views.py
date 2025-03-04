from django.contrib import messages
from django.db.models import QuerySet, Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.forms import PlantModelForm, PlantGroupModelForm, CauseOfDeathForm, \
    PlantTaskFrequencyGenericForm, PlantAndTaskGenericForm
from plant_care.models import Plant, PlantGroup, PlantGraveyard, PlantTaskFrequency


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

    def get_context_data(self, **kwargs) -> dict:
        """Overrides parent method get_context_data, adds 'task_frequencies' to context."""
        context = super().get_context_data(**kwargs)
        plant = self.get_object()

        task_frequencies = PlantTaskFrequency.objects.filter(plant=plant)
        context["task_frequencies"] = task_frequencies

        return context


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
        If the form is validated, calls the 'move_to_graveyard' method on the plant object to mark it as dead, records the cause of death and moves it to the 'graveyard'.
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


def plant_create_functional_view(request):
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


"""class PlantAndTaskFrequencyCreateView(CreateView):
    """"""
    model = Plant
    form_class = PlantModelForm
    template_name = "plant_create_page_template.html"
    success_url = reverse_lazy("plant_care:plant-list")

    def get_context_data(self, **kwargs) -> dict:
        """"""
        context = super().get_context_data(**kwargs)
        if self.request == "POST":
            context["task_frequency_form"] = PlantTaskFrequencyGenericForm(self.request.POST)
        else:
            context["task_frequency_form"] = PlantTaskFrequencyGenericForm()

        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """"""
        response = super().form_valid(form)  # saving the plant object
        task_frequency_form = PlantTaskFrequencyGenericForm(self.request.POST)

        if task_frequency_form.is_valid():
            task_frequency_form.save(self.object)

        return response"""

"""class PlantAndTaskFrequencyUpdateView(UpdateView):
    """"""
    model = Plant
    template_name = "plant_update_page_template.html"
    success_url = reverse_lazy("plant_care:plant-list")
    form_class = PlantModelForm

    def get_context_data(self, **kwargs) -> dict:
        """"""
        context = super().get_context_data(**kwargs)
        if self.request == "POST":
            context["task_frequency_form"] = PlantTaskFrequencyGenericForm(self.request.POST)
        else:
            context["task_frequency_form"] = PlantTaskFrequencyGenericForm()
        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """"""
        response = super().form_valid(form)
        task_frequency_form = PlantTaskFrequencyGenericForm(self.request.POST)

        if task_frequency_form.is_valid():
            for task, task_display in TASK_CATEGORY_CHOICES:
                frequency = task_frequency_form.cleaned_data.get(task)

                if frequency is not None:
                    # is there already some existing data for a given task_type?
                    task_existing_frequency = PlantTaskFrequency.objects.filter(plant=self.object, task_type=task).first()

                    if task_existing_frequency:
                        # if yes data already exists, update the frequency
                        task_existing_frequency.frequency = frequency
                        task_existing_frequency.save()
                    else:
                        # if not, make a new PlantTaskFrequency object
                        PlantTaskFrequency.objects.create(plant=self.object, task_type=task, frequency=frequency)

        return response"""


class PlantAndTaskFrequencyCreateGenericFormView(FormView):
    """"""
    template_name = "plant_create_page_template.html"
    form_class = PlantAndTaskGenericForm
    success_url = reverse_lazy("plant_care:plant-list")

    def form_valid(self, form) -> HttpResponseRedirect:
        """"""
        plant = Plant.objects.create(
            name=form.cleaned_data["name"],
            group=PlantGroup.objects.get(pk=form.cleaned_data["group"]),
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

        return super().form_valid(form)


class PlantAndTaskFrequencyUpdateGenericFormView(FormView):
    """"""
    template_name = "plant_update_page_template.html"
    form_class = PlantAndTaskGenericForm
    success_url = reverse_lazy("plant_care:plant-list")

    def get_form_kwargs(self) -> dict:
        """"""
        form_kwargs = super().get_form_kwargs()
        plant_id = self.kwargs.get("pk")
        plant = get_object_or_404(Plant, pk=plant_id)
        form_kwargs["plant"] = plant

        initial_data = {
            "name": plant.name,
            "group": plant.group if plant.group else None,
            "date": plant.date,
            "notes": plant.notes,
        }

        # Inicializace hodnot pro tasky
        for task, task_display in TASK_CATEGORY_CHOICES:
            existing_task = plant.task_frequencies.filter(task_type=task).first()
            if existing_task:
                initial_data[task] = existing_task.frequency

        form_kwargs["initial"] = initial_data  # Předání inicializačních dat
        return form_kwargs

    def form_valid(self, form) -> HttpResponseRedirect:
        """"""
        plant = get_object_or_404(Plant, pk=self.kwargs.get("pk"))
        plant.name = form.cleaned_data["name"]
        plant.group = form.cleaned_data["group"]
        plant.date = form.cleaned_data["date"]
        plant.notes = form.cleaned_data["notes"]
        plant.save()

        for task, task_display in TASK_CATEGORY_CHOICES:
            frequency = form.cleaned_data.get(task)
            task_existing = PlantTaskFrequency.objects.filter(plant=plant, task_type=task).first()
            if frequency:
                if task_existing:
                    task_existing.frequency = frequency
                    task_existing.save()

                else:
                    # if task frequency was not previously set, but it was added during update
                    PlantTaskFrequency.objects.create(
                        plant=plant,
                        task_type=task,
                        frequency=frequency
                    )
            else:
                # if field is left empty, set to default
                default_frequency = TASK_FREQUENCIES.get(task, None)
                if task_existing:
                    if default_frequency is not None:
                        task_existing.frequency = default_frequency
                        task_existing.save()
                    else:
                        task_existing.delete()  # for optional tasks - delete if there is no default frequency in constants

        return super().form_valid(form)
