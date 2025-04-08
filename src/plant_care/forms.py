from django import forms
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from plant_care.constants import CAUSE_OF_DEATH_CHOICES, TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.models import Plant, PlantGroup, PlantCareHistory


class PlantGroupModelForm(forms.ModelForm):
    """
    Form to update and create PlantGroup objects.
    """

    class Meta:
        model = PlantGroup
        fields = '__all__'

        labels = {
            'group_name': 'Group name',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }

    def clean_group_name(self):
        """
        Capitalizes the group name before saving.
        """
        group_name = self.cleaned_data.get('group_name')
        if group_name:
            group_name = group_name.capitalize()

        return group_name


class CauseOfDeathForm(forms.Form):
    """
    Form to allow user to choose the cause of death for a plant when marking it as dead.
    """
    cause_of_death = forms.ChoiceField(choices=CAUSE_OF_DEATH_CHOICES, required=True)


class BasePlantAndTaskGenericForm(forms.Form):
    """
    Base form for creating and updating Plant and PlantTaskFrequency objects at the same time.
    """
    name = forms.CharField(
        label="Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    group = forms.ModelChoiceField(
        label="Group",
        queryset=PlantGroup.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
    )
    date = forms.DateField(
        label="Date of purchase",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=date.today,
    )
    notes = forms.CharField(
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control"}),
        required=False,
    )

    def __init__(self, *args, **kwargs) -> None:
        """
        Dynamically generates frequency fields for each task type in TASK_CATEGORY_CHOICES.
        """
        super().__init__(*args, **kwargs)

        for task, task_display in TASK_CATEGORY_CHOICES:
            self.fields[task] = forms.IntegerField(
                required=False,
                label=f"{task} frequency (in days)",
                widget=forms.NumberInput(attrs={"class": "form-control",
                                                "placeholder": "Optional" if TASK_FREQUENCIES.get(
                                                    task) is None else ""}),
            )

    def clean_name(self):
        """
        Custom validation for name field when creating a new plant.
        Makes sure no duplicate plant names for living plants are created and titles the name.
        """
        name = self.cleaned_data.get("name")

        if name:
            name = name.title()

        if hasattr(self, "plant"): # if it's an update
            if self.plant.name.lower() != name.lower():
                if Plant.objects.filter(is_alive=True, name__iexact=name).exists():
                    raise ValidationError("Plant with this name already exists.")
        else:
            if Plant.objects.filter(is_alive=True, name__iexact=name).exists():
                raise ValidationError("Plant with this name already exists.")

        return name


class PlantTaskGenericForm(forms.Form):
    """
    Form for performing plant care tasks - creating PlantCareHistory records for selected plants.
    Includes task type selection, plant selection, and optional task date and time.
    """
    task_type = forms.MultipleChoiceField(
        choices=[(key, key) for key, value in TASK_CATEGORY_CHOICES],
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    plants = forms.ModelMultipleChoiceField(
        queryset=Plant.objects.filter(is_alive=True),
        widget=forms.CheckboxSelectMultiple,
    )

    task_date = forms.DateTimeField(
        label="Task date and time",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        initial=timezone.localtime(timezone.now()).replace(second=0)
    )

    def clean_task_date(self) -> datetime:
        """
        Validates that the task date is not in the future. Raises ValidationError if it is.
        """
        task_date = self.cleaned_data.get('task_date')

        if task_date and task_date > timezone.localtime(timezone.now()):
            raise forms.ValidationError("Task date cannot be in the future.")

        return task_date


class PlantCareHistoryModelForm(forms.ModelForm):
    """
    ModelForm for updating PlantCareHistory records.
    """

    class Meta:
        model = PlantCareHistory

        fields = [
            "task_type",
            "task_date",
        ]

        labels = {
            "task_type": "Task",
            "task_date": "Date",
        }

        widgets = {
            "task_type": forms.Select(attrs={"class": "form-control"}),
            "task_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),

        }

    def __init__(self, *args, **kwargs) -> None:
        """
        Changes task_type form field to show base value instead of display value.
        """
        super().__init__(*args, **kwargs)

        self.fields["task_type"].choices = [(display, category) for category, display in TASK_CATEGORY_CHOICES]
