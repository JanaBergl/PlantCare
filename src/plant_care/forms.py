from django import forms
from datetime import date
from plant_care.constants import CAUSE_OF_DEATH_CHOICES, TASK_CATEGORY_CHOICES, TASK_FREQUENCIES
from plant_care.models import Plant, PlantGroup, PlantTaskFrequency


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


class PlantAndTaskGenericForm(forms.Form):
    """
    Generic form to create and update Plant and PlantTaskFrequency objects at once.
    """
    name = forms.CharField(
        label='Name',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    group = forms.ModelChoiceField(
        label='Group',
        queryset=PlantGroup.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )
    date = forms.DateField(
        label='Date of purchase',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=date.today,

    )
    notes = forms.CharField(
        label='Notes',
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        required=False,
    )

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the form with optional plant data for update view.
        If a 'plant' instance is provided (update view), the form initializes task frequencies with existing values or default values from 'TASK_FREQUENCIES'.
        If not (create view), initializes tasks with default values.
        """
        self.plant = kwargs.pop("plant",
                                None)  # __init__ vadil neocekavany argument 'plant', nic jineho nefungovalo. 'plant' potrebuju dale, ale nesmi zustat v init
        super().__init__(*args, **kwargs)

        if self.plant:  # if update view
            for task, task_display in TASK_CATEGORY_CHOICES:
                existing_task = self.plant.task_frequencies.filter(task_type=task).first()
                if existing_task:
                    initial_value = existing_task.frequency
                else:
                    initial_value = TASK_FREQUENCIES.get(task, None)

                self.fields[task] = forms.IntegerField(
                    required=False,
                    initial=initial_value if initial_value is not None else TASK_FREQUENCIES.get(task, None),
                    label=f"{task} frequency (in days)",
                    widget=forms.NumberInput(
                        attrs={'class': 'form-control', 'placeholder': 'Optional' if initial_value is None else None})
                )
        else:
            # if create view
            for task, task_display in TASK_CATEGORY_CHOICES:
                initial_value = TASK_FREQUENCIES.get(task, None)

                self.fields[task] = forms.IntegerField(
                    required=False,
                    initial=initial_value,
                    label=f"{task} frequency (in days)",
                    widget=forms.NumberInput(
                        attrs={'class': 'form-control', 'placeholder': 'Optional' if initial_value is None else None})
                )


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

    def __init__(self, *args, **kwargs):
        """"""
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

    def __init__(self, *args, **kwargs) -> None:
        self.plant = kwargs.pop('plant', None)
        super().__init__(*args, **kwargs)


class PlantTaskGenericForm(forms.Form):
    """
    https://docs.djangoproject.com/en/4.2/ref/forms/fields/
    """
    task_type = forms.MultipleChoiceField(
        choices=[(key, key) for key, value in TASK_CATEGORY_CHOICES],  # otherwise RadioSelect uses the display value
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    plants = forms.ModelMultipleChoiceField(
        queryset=Plant.objects.filter(is_alive=True),
        widget=forms.CheckboxSelectMultiple,
    )
