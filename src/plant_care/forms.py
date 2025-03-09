from django import forms
from datetime import date, datetime

from django.core.exceptions import ValidationError
from plant_care.constants import CAUSE_OF_DEATH_CHOICES, TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.models import Plant, PlantGroup, PlantTaskFrequency, PlantCareHistory, validate_plant_unique_name


class PlantModelForm(forms.ModelForm):
    """
    Form to create and update Plant objects.
    """

    class Meta:
        model = Plant
        fields = [
            'name',
            'group',
            'date',
            'notes',
        ]

        labels = {
            'name': 'Name',
            'group': 'Group',
            'date': 'Date of purchase',
            'notes': 'Notes',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
        }


class PlantGroupModelForm(forms.ModelForm):
    """
    Form to update and create PlantGroup objects
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


class CauseOfDeathForm(forms.Form):
    """
    Form to allow user to choose the cause of death for a plant.
    """
    cause_of_death = forms.ChoiceField(choices=CAUSE_OF_DEATH_CHOICES, required=True)


class PlantTaskFrequencyGenericForm(forms.Form):
    """"""

    def __init__(self, *args, **kwargs) -> None:
        """
        Generates the form fields according to TASK_CATEGORY_CHOICES. Fills the field with exiting data if there is available.
        """
        super().__init__(*args, **kwargs)
        for task, task_display in TASK_CATEGORY_CHOICES:
            initial_frequency = TASK_FREQUENCIES.get(task, None)

            self.fields[task] = forms.IntegerField(
                required=False,
                initial=initial_frequency,
                label=f"{task} frequency (in days)",
                widget=forms.NumberInput(
                    attrs={'class': 'form-control', 'placeholder': 'Optional' if initial_frequency is None else None})
            )

    def save(self, plant) -> None:
        """
        Saves the task frequency data for a given plant. If a frequency is not provided, default one from TASK_FREQUENCIES is saved.
        If a valid frequency is found, a PlantTaskFrequency object is created and saved for the given plant.

        :param plant: The Plant instance to associate the task frequencies with.
        """
        # "Watering", "watered"
        for task, task_display in TASK_CATEGORY_CHOICES:
            frequency = self.cleaned_data.get(task)
            if frequency is None:
                frequency = TASK_FREQUENCIES.get(task, None)

            if frequency is not None:
                PlantTaskFrequency.objects.create(
                    plant=plant,
                    task_type=task,
                    frequency=frequency
                )


class BasePlantAndTaskGenericForm(forms.Form):
    """
    Base form for creating and updating Plant and PlantTaskFrequency objects at the same time.
    """
    name = forms.CharField(
        label="Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[validate_plant_unique_name]
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

    def __init__(self, *args, **kwargs):
        """
        Dynamically creates fields for user to fill out based on every task_type in TASK_CATEGORY_CHOICES.
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


class PlantAndTaskGenericUpdateForm(BasePlantAndTaskGenericForm):
    """
    Form based on parent 'BasePlantAndTaskForm' to update Plant and PlantTaskFrequency objects at the same time.
    https://forum.djangoproject.com/t/using-request-user-in-forms-py/19184/4 - pop z init?
    """

    # BEZ POP A PRI POUZIVANI GET_INITIAL V UPDATE VZDY CHYBA TypeError at /plants/update-plant/22/
    # BaseForm.__init__() got an unexpected keyword argument 'plant'
    # Request Method:	POST
    # -> jedine co zatim funguje je toto s .pop

    def __init__(self, *args, **kwargs) -> None:
        self.plant = kwargs.pop('plant', None)
        super().__init__(*args, **kwargs)


class PlantTaskGenericForm(forms.Form):
    """
    Generic form for performing plant care tasks - creating PlantCareHistory records for selected plants.
    Includes task type selection, plant selection, and optional task date and time.
    """
    task_type = forms.MultipleChoiceField(
        choices=[(key, key) for key, value in TASK_CATEGORY_CHOICES],  # jinak z choice bere vzdy display
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
        initial=datetime.now()
    )

    def clean_task_date(self) -> datetime:
        """
        Validates that the task date is not in the future.
        """
        task_date = self.cleaned_data.get('task_date')
        if task_date > datetime.now():
            raise forms.ValidationError("Task date cannot be in the future.")

        return task_date


class PlantCareHistoryModelForm(forms.ModelForm):
    """
    pro testovaci data, jinak odstranit, moznost upravy zaznamu historie neni nutna
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
            "task_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

        }

    def __init__(self, *args, **kwargs):
        """

        """
        plant = kwargs.pop('plant', None)
        super().__init__(*args, **kwargs)

        if plant:
            self.instance.plant = plant
