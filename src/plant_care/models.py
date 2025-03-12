from django.urls import reverse_lazy
import datetime
from django.db import models
from django.utils import timezone
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES, CAUSE_OF_DEATH_CHOICES


class PlantGroup(models.Model):
    """
    Represents a group or a category of plants.

    Fields:
        - group_name (string): Unique name of the group.
    """
    group_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return f"{self.group_name}"

    def __repr__(self) -> str:
        return f"PlantGroup(group_name={self.group_name})"

    def delete(self, *args, **kwargs) -> None:
        """
        Makes sure that default group 'Uncategorized' cannot be deleted.
        If another group is deleted, all plants in that group are reassigned to default 'Uncategorized'

        :raises ValueError: If user tries to delete 'Uncategorized' group.
        """
        if self.group_name == "Uncategorized":
            raise ValueError("The 'Uncategorized' group cannot be deleted.")

        plants_in_group = Plant.objects.filter(group=self)
        for plant in plants_in_group:
            plant.group = None
            plant.save()

        super().delete(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the absolute url to the plant group detail view.
        """
        return reverse_lazy("plant_care:plant-group-detail", kwargs={"pk": self.id})


class Plant(models.Model):
    """
    Represents a plant, with fields: name, group, date of purchase, notes, and its current status (alive or not).

    Fields:
        - name (string): Name of the plant.
        - group (PlantGroup): Optional group to which the plant belongs (ForeignKey to PlantGroup). If not provided, set to default 'Uncategorized'.
        - date (datetime.date): Date of purchase.
        - notes (string): Optional additional notes about the plant.
        - is_alive (bool): Status of the plant - alive or not.
    """
    name = models.CharField(max_length=100)
    group = models.ForeignKey(PlantGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="plants")
    date = models.DateField(default=datetime.date.today)
    notes = models.TextField(null=True, blank=True)
    is_alive = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Plant(name={self.name}, date={self.date}, group={self.group}, notes={self.notes}, is_alive={self.is_alive})"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides parent 'save' method and sets a default group to 'Uncategorized' if not provided by user.
        If 'Uncategorized' group does not exist, it will be created.
        """
        if self.group is None:
            self.group = PlantGroup.objects.get_or_create(group_name='Uncategorized')[0]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the absolute url to the plant detail view.
        """
        return reverse_lazy("plant_care:plant-detail", kwargs={"pk": self.id})

    def move_to_graveyard(self, reason: str) -> None:
        """
        Moves a plant to a graveyard, changes its 'is_alive' field to False.

        :param reason: A string representing the cause of death of the plant.
        """
        if not self.is_alive:
            return

        self.is_alive = False
        self.save()
        PlantGraveyard.objects.create(plant=self, cause_of_death=reason)


class PlantCareHistory(models.Model):
    """
    Represents the care history of a plant, recording the type of task performed, the date when the task was done, and the related plant.

    Fields:
        - plant (Plant): The plant object related to the care history (ForeignKey to the Plant model).
        - task_type (string): The type of task performed (based on TASK_CATEGORY_CHOICES).
        - task_date (datetime): The date and time when the task was performed.
        """

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=25, choices=TASK_CATEGORY_CHOICES)
    task_date = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.plant.name} has been {self.get_task_type_display()} on {self.task_date.strftime('%d-%m-%Y %H:%M')}"

    def __repr__(self) -> str:
        return f"PlantCareHistory(plant={self.plant.id}, task_type='{self.task_type}', task_date={self.task_date})"

    def formatted_task_date(self) -> str:
        """
        Formats the task date into a specific string format considering the timezone.

        :return: A string representing the task date formatted as "%d/%m/%Y %H:%M"
        """
        local_task_date = timezone.localtime(self.task_date)

        return local_task_date.strftime("%d/%m/%Y %H:%M")


def get_default_frequency(task_type) -> int | None:
    """
    Returns the default frequency for a task from the 'TASK_FREQUENCIES' dictionary.

    :param task_type: The type of task for which the frequency is requested.

    :return: The default frequency for a given task type or None if not found.
    """
    return TASK_FREQUENCIES.get(task_type, None)


class PlantTaskFrequency(models.Model):
    """
    Represents the frequency at which a specific task should be performed for a particular plant.

    Fields:
        - plant (Plant): The plant associated with the task frequency (ForeignKey to the Plant model).
        - task_type (string): The type of task (based on TASK_CATEGORY_CHOICES).
        - frequency (int): The number of allowed days between each task. If not set, default frequency is used from TASK_FREQUENCIES.
    """

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name="task_frequencies")
    task_type = models.CharField(max_length=25, choices=TASK_CATEGORY_CHOICES)
    frequency = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.plant.name} should be {self.get_task_type_display()} every {self.frequency} days" if self.frequency else f"{self.plant.name} has no specific schedule for {self.task_type.lower()}"

    def __repr__(self) -> str:
        return f"PlantTaskFrequency(plant={self.plant.name}, task_type={self.task_type}, frequency={self.frequency})"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides parent 'save' method and sets a default frequency if not provided by user.
        """
        if self.frequency is None:
            self.frequency = get_default_frequency(self.task_type)
        super().save(*args, **kwargs)


class PlantGraveyard(models.Model):
    """
    Represents the 'graveyard' where dead plants are moved.

    Fields:
        - plant (Plant): The plant associated with the graveyard entry (OneToOneField to the Plant model).
        - date_of_death (datetime): The date of the plants' death.
        - cause_of_death (string): Optional cause of death for the plant, chosen from CAUSE_OF_DEATH_CHOICES. If not provided, default "unknown" is used.
    """

    plant = models.OneToOneField(Plant, on_delete=models.CASCADE)
    date_of_death = models.DateField(auto_now_add=True)
    cause_of_death = models.CharField(max_length=50, blank=True, null=True, choices=CAUSE_OF_DEATH_CHOICES,
                                      default='unknown')

    def __str__(self) -> str:
        return f"{self.plant.name} died on {self.date_of_death.strftime('%d/%m/%Y')} due to {self.cause_of_death}"

    def __repr__(self) -> str:
        return f"PlantGraveyard(plant= {self.plant.name}({self.plant.id}), date_of_death={self.date_of_death!r}, cause_of_death={self.cause_of_death})"
