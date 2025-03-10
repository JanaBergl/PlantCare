from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet, Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.forms import PlantGroupModelForm, CauseOfDeathForm, PlantTaskGenericForm, \
    PlantAndTaskGenericUpdateForm, BasePlantAndTaskGenericForm, PlantCareHistoryModelForm
from plant_care.models import Plant, PlantGroup, PlantGraveyard, PlantTaskFrequency, PlantCareHistory, \
    get_default_frequency
from plant_care.utils import show_care_warnings


# HOME PAGE_____________________________________________________________________________________________________________
class HomePageTemplateView(LoginRequiredMixin, TemplateView):
    """
    View to display the home page of the app.
    """
    template_name = "home_page.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'user_name' to context.
        Adds 'overdue_plant_count' to context to show how many plants need care on the home page.
        """
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username

        overdue = show_care_warnings()
        plants_requiring_care = set()

        for warning in overdue:
            plants_requiring_care.add(warning["plant"])

        context["overdue_plant_count"] = len(plants_requiring_care)

        return context


# LIST VIEWS____________________________________________________________________________________________________________
class PlantListingView(LoginRequiredMixin, ListView):
    """
    View for displaying the list of living plants.
    """
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, filters only living plants.
        Allows user to filter by name or group and sort list by plant name, group name or date of purchase in ascending or descending order.
        """
        queryset = super().get_queryset().filter(is_alive=True)

        search = self.request.GET.get("filter")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(group__group_name__icontains=search)
            )

        ordering = self.request.GET.get("sort", "name")
        if ordering.lstrip("-") not in ["name", "group__group_name", "date"]:
            ordering = "name"

        return queryset.order_by(ordering)


class PlantGroupListingView(LoginRequiredMixin, ListView):
    """
    View for displaying the list of plant groups.
    """
    model = PlantGroup
    context_object_name = "groups"
    template_name = "plant_group_listing_page_template.html"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, counts the number of living plants in each group.
        Allows user to sort list by group name or number of plants in a group in ascending or descending order.
        """
        queryset = PlantGroup.objects.annotate(
            num_plants=Count("plants", filter=Q(plants__is_alive=True))
        )

        ordering = self.request.GET.get("sort", "group_name")
        if ordering.lstrip("-") in ["group_name", "num_plants"]:
            return queryset.order_by(ordering)

        return queryset

    """ moznost 2
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for group in context["groups"]:
            group.num_plants = group.plants.filter(is_alive=True).count()
        return context
    """


class PlantsInGroupListingView(LoginRequiredMixin, ListView):
    """
    View for displaying a list of plants in a specific group.
    """
    model = Plant
    context_object_name = "plants"
    template_name = "plant_listing_page_template.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'group' to context.
        """
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)
        context["group"] = group

        return context

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method get_queryset, filters only alive plants inside a given group
        and allows sorting by plant name or date of purchase in ascending or descending order.
        """
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)

        queryset = Plant.objects.filter(group=group, is_alive=True)

        ordering = self.request.GET.get("sort", "name")
        if ordering.lstrip("-") not in ["name", "date"]:
            ordering = "name"

        return queryset.order_by(ordering)


class PlantGraveyardListingView(LoginRequiredMixin, ListView):
    """
    View for displaying the list of dead plants (plants in the graveyard).
    """
    model = PlantGraveyard
    template_name = "plant_graveyard_listing_page_template.html"
    context_object_name = "graveyard"

    def get_queryset(self) -> QuerySet:
        """
        Allows user to sort list by name, cause of death or date of death in ascending or descending order.
        """
        queryset = super().get_queryset()

        ordering = self.request.GET.get("sort", "plant__name")

        if ordering.lstrip("-") not in ["plant__name", "cause_of_death", "date_of_death"]:
            ordering = "plant__name"

        return queryset.order_by(ordering)


class PlantCareHistoryListingView(LoginRequiredMixin, ListView):
    """
    View for a list of plant care history logs.

    """
    model = PlantCareHistory
    template_name = "plant_care_history_listing_page_template.html"
    context_object_name = "history"

    def get_queryset(self) -> QuerySet:
        """
        Overrides parent method 'get_queryset', adds initial data for the plant care history logs ordered by date.
        Allows user to search by plant/group name/task type and filter history logs for the last day/week/month.
        """
        queryset = PlantCareHistory.objects.select_related('plant').order_by("-task_date")

        # pres odkaz puvodne v detailview je filter v kwargs (URL parametry) ->self.kwargs.get("filter")
        # pres search bar je v request.GET - GET parametry -> zmena oboje na GET, neni nutne dvakrat enter ZKONTROLOVAT

        search = self.request.GET.get("filter")
        if search:
            queryset = queryset.filter(
                Q(task_type__icontains=search) |
                Q(plant__group__group_name__istartswith=search) |
                Q(plant__name__istartswith=search)
            ).distinct()


        # __gte = Django ORM greater than
        time = self.request.GET.get("time")
        if time:
            now = timezone.now()
            if time == "day":
                queryset = queryset.filter(task_date__gte=now - timedelta(days=1))
            elif time == "week":
                queryset = queryset.filter(task_date__gte=now - timedelta(weeks=1))
            elif time == "month":
                queryset = queryset.filter(task_date__gte=now - timedelta(days=30))

        return queryset


# DETAIL VIEWS__________________________________________________________________________________________________________
class PlantDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying specific plant details.
    """
    model = Plant
    template_name = "plant_detail_page_template.html"
    context_object_name = "plant"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds task_frequencies and warnings to context.
        """
        context = super().get_context_data(**kwargs)
        plant = self.get_object()

        task_frequencies = PlantTaskFrequency.objects.filter(plant=plant)
        context["task_frequencies"] = task_frequencies

        warnings = show_care_warnings()
        plant_warnings = [warning for warning in warnings if warning["plant"] == plant]
        context["plant_warnings"] = plant_warnings

        return context


class PlantGroupDetailView(LoginRequiredMixin, DetailView):
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


# CREATE VIEWS__________________________________________________________________________________________________________
class PlantGroupCreateView(LoginRequiredMixin, CreateView):
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


class PlantAndTaskFrequencyCreateGenericFormView(LoginRequiredMixin, FormView):
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
            initial_data[task] = get_default_frequency(task)

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


# UPDATE VIEWS__________________________________________________________________________________________________________
class PlantGroupUpdateView(LoginRequiredMixin, UpdateView):
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


class PlantAndTaskFrequencyUpdateGenericFormView(LoginRequiredMixin, FormView):
    """
    View for updating a plant and its related task frequencies.
    """
    template_name = "plant_update_page_template.html"
    form_class = PlantAndTaskGenericUpdateForm

    def get_form_kwargs(self) -> dict:
        """
        Adds the plant object and initial data to the form.
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
                initial_data[task] = get_default_frequency(task)

        form_kwargs["initial"] = initial_data
        return form_kwargs

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Overrides parent method 'form_valid' to handle the form submisson and update the plant
        and task frequency objects.
        """

        plant = form.plant  # TADY POTREBUJU PLANT OBJEKT, MUSIM HO ZISKAT Z FORM. PRES GET INITAL VZDY CHYBA

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
                # if field is left empty, delete the task frequency
                task_existing.delete()

        self.plant = plant

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Returns the URL to the detail view of the newly updated plant.
        """
        return self.plant.get_absolute_url()


class NEFUNGUJEPlantAndTaskFrequencyUpdateGenericFormView(LoginRequiredMixin, FormView):
    """
    # BEZ kwargs.pop("plant") v init formu nefunguje. PRI POUZIVANI GET_INITIAL V UPDATE VZDY CHYBA TypeError at /plants/update-plant/22/
    # BaseForm.__init__() got an unexpected keyword argument 'plant'
    # Request Method:	POST
    # -> jedine co zatim funguje je verze vyse a .pop v init formulare
    """
    template_name = "plant_update_page_template.html"
    form_class = BasePlantAndTaskGenericForm

    def get_initial(self) -> dict:
        """
        Overrides parent method get_initial, adds initial data for the plant and its task frequencies.
        """
        initial_data = super().get_initial()
        plant_id = self.kwargs.get("pk")
        plant = get_object_or_404(Plant, pk=plant_id)

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
                initial_data[task] = get_default_frequency(task)

        return initial_data

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


class PlantCareHistoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating a plant care history record.
    """
    template_name = "plant_history_log_update_page_template.html"
    model = PlantCareHistory
    success_url = reverse_lazy("plant_care:care-history")
    form_class = PlantCareHistoryModelForm

    def form_valid(self, form):
        """
        Makes sure that task_date is timezone-aware before saving.
        """
        task_date = form.cleaned_data.get("task_date")
        if task_date and timezone.is_naive(task_date):
            task_date = timezone.make_aware(task_date)

        form.instance.task_date = task_date

        return super().form_valid(form)


# DELETE VIEWS__________________________________________________________________________________________________________
class PlantDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting an existing plant.
    """
    template_name = "plant_delete_page_template.html"
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


class PlantGroupDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting an existing plant group.
    'Uncategorized' group cannot be deleted.
    """
    template_name = "plant_group_delete_page_template.html"
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


class PlantCareHistoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting a plant care history log.
    """
    model = PlantCareHistory
    success_url = reverse_lazy("plant_care:care-history")
    template_name = "plant_care_history_delete_page_template.html"
    context_object_name = "history"


# CUSTOM VIEWS__________________________________________________________________________________________________________
class DeadPlantView(LoginRequiredMixin, FormView):
    """
    View for marking a plant as dead (is_alive=False).
    """
    template_name = "plant_dead_page_template.html"
    form_class = CauseOfDeathForm
    success_url = reverse_lazy("plant_care:plant-graveyard-list")

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method get_context_data, adds 'plant' to context.
        """
        context = super().get_context_data(**kwargs)

        plant_id = self.kwargs.get('pk')
        context["plant"] = get_object_or_404(Plant, pk=plant_id)
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


class PerformTaskView(LoginRequiredMixin, FormView):
    """
    View for performing a task. User can select one or more plants, select a date and time and perform one or more tasks.
    Creates PlantCareHistory objects.
    """
    template_name = "plant_perform_tasks_list_page_template.html"
    form_class = PlantTaskGenericForm
    success_url = reverse_lazy("plant_care:care-history")

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds only living plants to the context.
        Adds a list of plants with active warnings for overdue tasks.
        """
        context = super().get_context_data(**kwargs)
        context["plants"] = Plant.objects.filter(is_alive=True)

        context["plants_in_danger"] = {plant["plant"].id for plant in show_care_warnings()}

        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Handles the valid form submission, creating PlantCareHistory objects for each selected plant and task.
        If no task date is provided, current date and time is used.
        """
        task_types = form.cleaned_data.get("task_type")
        plant_list = form.cleaned_data.get("plants")
        task_date = form.cleaned_data.get("task_date", timezone.now())

        for plant in plant_list:
            for task_type in task_types:
                PlantCareHistory.objects.create(
                    plant=plant,
                    task_type=task_type,
                    task_date=task_date,
                )
        return super().form_valid(form)


class PlantCareOverdueWarningsView(LoginRequiredMixin, TemplateView):
    """
    View to display overdue care warnings for plants based on their task frequency.
    If a task has never been done before, then the plant care warning is not displayed.
    """
    template_name = "plant_task_overdue_warnings.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Overrides parent method 'get_context_data', adds overdue care warnings for plants to the context.
        Allows sorting of care warnings table by plant or group name, task type or number of days overdue.
        """
        context = super().get_context_data(**kwargs)
        warnings = show_care_warnings()

        sort_by = self.request.GET.get("sort", "plant.name")
        reverse = False
        if sort_by.startswith("-"):
            reverse = True
            sort_by = sort_by.lstrip("-")

        if sort_by == "group":
            warnings = sorted(warnings, key=lambda x: x["group"].group_name, reverse=reverse)
        elif sort_by == "task":
            warnings = sorted(warnings, key=lambda x: x["task_type"], reverse=reverse)
        elif sort_by == "days_overdue":
            warnings = sorted(warnings, key=lambda x: x["days_since_task"], reverse=reverse)
        else:
            warnings = sorted(warnings, key=lambda x: x["plant"].name, reverse=reverse)

        context["warnings"] = warnings
        return context


# NA SMAZANI ?__________________________________________________________________________________________________________
class Error404PageTemplateView(TemplateView):
    """
    zkouska custom 404 page not found stranky, smazat!
    """
    template_name = "404.html"




