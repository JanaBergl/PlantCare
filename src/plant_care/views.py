from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet, Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.forms import PlantGroupModelForm, CauseOfDeathForm, PlantTaskGenericForm, BasePlantAndTaskGenericForm, PlantCareHistoryModelForm
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
        Adds additional context data to be displayed on the home page.

        Context includes:
            - user_name: Username of the logged-in user
            - overdue_plant_count: The number of plants requring care
            - overdue_task_count: The number of overdue tasks
            - number_of_plants: Total number of living plants in the database
            - history_records: The number of tasks completed in the past 30 days
        """
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username

        overdue = show_care_warnings()
        plants_requiring_care = set()

        for warning in overdue:
            plants_requiring_care.add(warning["plant"])

        context["overdue_plant_count"] = len(plants_requiring_care)

        context["overdue_task_count"] = len(overdue)

        context["number_of_plants"] = Plant.objects.filter(is_alive=True).count()

        context["history_records"] = PlantCareHistory.objects.filter(
            task_date__gte=timezone.now() - timedelta(days=30)).count()

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
        Allows user to filter and sort the list of living plants.

        Filters:
            - only includes living plants
            - allows search by name or group name if 'filter' is provided in GET.

        Sorting:
            - default sorting by plant name
            - supports sorting by plant name, group name or date of purchase if 'sort' is provided in GET.
            - allows changing between ascending or descending order
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
        Allows user to sort the list of plant groups. Annotates each group with the count of living plants in it.

        Annotation:
            - num_plants: total count of living plants in a group

        Sorting:
            - default sorting by group name
            - supports sorting by group name or number of plants in a group if 'sort' is provided in GET.
            - allows changing between ascending or descending order
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
        Adds additional context data to the list of plants.

        Context includes:
            - group: The PlantGroup object of the listed plants
        """
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)
        context["group"] = group

        return context

    def get_queryset(self) -> QuerySet:
        """
        Allows user to filter and sort the list of living plants in a given group.

        Filters:
            - only includes living plants in the group
            - allows search by plant name if 'filter' is provided in GET.

        Sorting:
            - default sorting by plant name
            - supports sorting by plant name or date of purchase if 'sort' is provided in GET.
            - allows changing between ascending or descending order
        """
        group_id = self.kwargs.get("pk")
        group = get_object_or_404(PlantGroup, pk=group_id)

        queryset = Plant.objects.filter(group=group, is_alive=True)

        search = self.request.GET.get("filter")
        if search:
            queryset = queryset.filter(name__icontains=search)

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
        Allows user to sort the list of plants in the graveyard.

        Sorting:
            - default sorting by plant name
            - supports sorting by plant name, cause of death or date of death
            - allows changing between ascending or descending order
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
        Allows user to filter and sort the list of care history records.

        Filters:
            - allows search by task type, plant or group name if 'filter' is provided in GET.
            - allows filtering by time period (day, week, or month) if 'time' is provided in GET.

        Sorting:
            - default sorting by task date (most recent first).
        """
        queryset = PlantCareHistory.objects.select_related('plant').order_by("-task_date")

        search = self.request.GET.get("filter")
        if search:
            queryset = queryset.filter(
                Q(task_type__icontains=search) |
                Q(plant__group__group_name__istartswith=search) |
                Q(plant__name__istartswith=search)
            ).distinct()

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
        Adds additional context data to be displayed on the detail page.

        Context includes:
            - task_frequencies: A list of tasks frequencies associated with the plant.
            - plant_warnings: A list of plant warnings associated with the plant.
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
        Adds additional context data to be displayed on the group detail page.

        Context includes:
            - num_plants: Number of plants in the group.
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
        Adds initial data for task frequencies based on default TASK_FREQUENCIES choices.
        """
        form_kwargs = super().get_form_kwargs()

        initial_data = {}
        for task, task_display in TASK_CATEGORY_CHOICES:
            initial_data[task] = get_default_frequency(task)

        form_kwargs["initial"] = initial_data
        return form_kwargs

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Handles the process after the form is validated by user.
        After successful validation creates a new Plant object and its related PlantTaskFrequency objects.
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

        self.plant = plant  # saving the plant object for use in get_success_url

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

    def get_form(self, form_class=None):
        """
        Adds the plant object and initial data to the form.
        If there are no existing PlantTaskFrequency objects for the plant, default values are used.
        """
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

        if self.request.method == "POST":
            form = BasePlantAndTaskGenericForm(self.request.POST)
        else:
            form = BasePlantAndTaskGenericForm(initial=initial_data)

        form.plant = plant

        return form

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Handles the process after the form is validated by user.
        After successful validation updates an existing Plant object and updates, creates or deletes its related PlantTaskFrequency objects based on the form data.
        """

        plant = form.plant

        plant.name = form.cleaned_data["name"]
        plant.group = form.cleaned_data["group"]
        plant.date = form.cleaned_data["date"]
        plant.notes = form.cleaned_data["notes"]

        for task, task_display in TASK_CATEGORY_CHOICES:
            frequency = form.cleaned_data.get(task)
            task_existing = plant.task_frequencies.filter(task_type=task).first()

            if frequency is not None:
                if task_existing:
                    task_existing.frequency = frequency
                    task_existing.save()
                else:
                    # if task frequency was not previously set, but it was added now during update
                    PlantTaskFrequency.objects.create(plant=plant, task_type=task, frequency=frequency)
            elif task_existing:
                # if field is left empty, delete the task frequency
                task_existing.delete()

        plant.save()

        self.plant = plant  # saving the plant object for use in get_success_url
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
    View for deleting an existing plant group. All groups except for 'Uncategorized' can be deleted.
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
    View for marking a plant as dead (is_alive=False) by filling out a form with the cause of death and calling move_to_graveyard().
    """
    template_name = "plant_dead_page_template.html"
    form_class = CauseOfDeathForm
    success_url = reverse_lazy("plant_care:plant-graveyard-list")

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds Plant object to the context data.
        """
        context = super().get_context_data(**kwargs)

        plant_id = self.kwargs.get('pk')
        context["plant"] = get_object_or_404(Plant, pk=plant_id)

        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Handles the process after the form is validated by user.
        After successful validation, calls the 'move_to_graveyard' method on the plant object to mark it as dead, records the cause of death provided in the form and moves it to the 'graveyard'.
        """
        plant_id = self.kwargs['pk']
        plant = get_object_or_404(Plant, pk=plant_id)
        reason = form.cleaned_data.get('cause_of_death')

        plant.move_to_graveyard(reason)

        return super().form_valid(form)


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
        Adds additional data to the context. Allows filtering by plant name or group name if 'filter' is provided in GET.
        Allows sorting by plant or group name in ascending or descending order if 'sort' is provided in GET.

        Context includes:
            - plants: All living plants, filtered by name or group if 'filter' is provided in GET.
            - plants_in_danger: Set of plants with active warnings for overdue tasks.

        """
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get("filter", "")

        plants_queryset = Plant.objects.filter(is_alive=True)
        if search:
            plants_queryset = plants_queryset.filter(Q(name__icontains=search) | Q(group__group_name__icontains=search))

        sort_by = self.request.GET.get("sort", "name")
        reverse = False
        if sort_by.startswith("-"):
            reverse = True
            sort_by = sort_by.lstrip("-")

        if sort_by == "group":
            plants_queryset = plants_queryset.order_by("group__group_name" if not reverse else "-group__group_name")
        else:
            plants_queryset = plants_queryset.order_by("name" if not reverse else "-name")

        context["plants"] = plants_queryset
        context["plants_in_danger"] = {warning["plant"].id for warning in show_care_warnings()}

        return context

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Handles the valid form submission, creating PlantCareHistory objects for each selected plant and task.
        If no task date is provided, current date and time is used.
        """
        task_types = form.cleaned_data.get("task_type")
        plant_list = form.cleaned_data.get("plants")
        task_date = form.cleaned_data.get("task_date", timezone.now())

        if not timezone.is_aware(task_date):
            task_date = timezone.make_aware(task_date, timezone.get_current_timezone())

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
    If a task has never been done before, the plant care warning is not displayed.
    """
    template_name = "plant_task_overdue_warnings.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds additional data to the context.
        Allows sorting by plant or group name, task type or number of days overdue in ascending or descending order if 'sort' is provided in GET.

        Context includes:
            - warnings: list of warnings for overdue tasks based on plants task frequency and last record in care history.
        """
        context = super().get_context_data(**kwargs)
        warnings = show_care_warnings()

        sort_by = self.request.GET.get("sort", "-days_since_task")
        reverse = False

        if sort_by.startswith("-"):
            reverse = True
            sort_by = sort_by.lstrip("-")

        if sort_by == "plant":
            warnings = sorted(warnings, key=lambda x: x["plant"].name, reverse=reverse)
        elif sort_by == "group":
            warnings = sorted(warnings, key=lambda x: x["group"].group_name, reverse=reverse)
        elif sort_by == "task":
            warnings = sorted(warnings, key=lambda x: x["task_type"], reverse=reverse)
        elif sort_by == "days_overdue":
            warnings = sorted(warnings, key=lambda x: x["days_since_task"], reverse=reverse)
        else:
            warnings = sorted(warnings, key=lambda x: x["days_since_task"], reverse=reverse)

        context["warnings"] = warnings
        return context


# NA SMAZANI ?__________________________________________________________________________________________________________
class Error404PageTemplateView(TemplateView):
    """
    zkouska custom 404 page not found stranky, smazat!
    """
    template_name = "404.html"
