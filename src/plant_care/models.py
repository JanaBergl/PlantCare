from django.utils.timezone import now
from django.db import models
from plant_care.constants import TASK_CATEGORY_CHOICES, TASK_FREQUENCIES, CAUSE_OF_DEATH_CHOICES


class PlantGroup(models.Model):
    """
    Represents a group or a category of plants. Each group has a name and can
    be used to organize plants into different categories.
    """
    group_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return f"{self.group_name}"

    def __repr__(self) -> str:
        return f"PlantGroup(group_name={self.group_name})"


class Plant(models.Model):
    """
    Represents a plant, with attributes: name, group, date of purchase, notes, and its current status (alive or not).
    """
    name = models.CharField(max_length=100, unique=True)
    group = models.ForeignKey(PlantGroup, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=now)
    notes = models.TextField(null=True, blank=True)
    is_alive = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Plant(name={self.name}, date={self.date}, group={self.group}, notes={self.notes}, is_alive={self.is_alive})"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides parent 'self' method and sets a default group to 'Uncategorized' if not provided by user. If 'Uncategorized' group does not exist, it will be created.
        """
        if self.group is None:
            self.group = PlantGroup.objects.get_or_create(group_name='Uncategorized')[0]
        super().save(*args, **kwargs)

    def move_to_graveyard(self, reason: str) -> None:
        """
        Moves a plant to a graveyard, changes 'is_alive' parameter to False.

        :param reason: A string representing the cause of death of the plant.
        """
        if not self.is_alive:
            return

        self.is_alive = False
        self.save()
        PlantGraveyard.objects.create(plant=self, cause_of_death=reason)


class PlantCareHistory(models.Model):
    """
    Represents the care history of a plant, noting the type of task performed (watering, fertilizing, repotting),
    the date the task was done, and the related plant.
    """

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=20, choices=TASK_CATEGORY_CHOICES)
    task_date = models.DateTimeField(default=now)  # formát

    def __str__(self) -> str:
        return f"{self.plant.name} has been {self.get_task_type_display().lower()} on {self.task_date.strftime('%d-%m-%Y %H:%M')}"

    def __repr__(self) -> str:
        return f"PlantCareHistory(plant={self.plant.id}, task_type='{self.task_type}', task_date={self.task_date!r})"

    def formatted_task_date(self) -> str:
        """
        Formats the task date into a specific string format.

        :return: A string representing the task date formatted as "%d/%m/%Y %H:%M"
        """
        return self.task_date.strftime("%d/%m/%Y %H:%M")


def get_default_frequency(task_type) -> int | None:
    """
    Returns the default frequency for a task from the 'TASK_FREQUENCIES' dictionary.

    :return: The default frequency for a given task type or None
    """
    return TASK_FREQUENCIES.get(task_type, None)


class PlantTaskFrequency(models.Model):
    """
    Represents the frequency at which a specific task should be performed for a particular plant.
    """

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=20, choices=TASK_CATEGORY_CHOICES)
    frequency = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.plant.name} should be {self.get_task_type_display().lower()} every {self.frequency} days" if self.frequency else f"{self.plant.name} has no specific schedule for {self.get_task_type_display().lower()}"

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
    Represents the 'graveyard' where dead plants are moved. Stores the plant associated with the graveyard entry, the date of death, and optional cause of death.
    """

    plant = models.OneToOneField(Plant, on_delete=models.CASCADE)
    date_of_death = models.DateField(auto_now_add=True)  # formát
    cause_of_death = models.CharField(max_length=50, blank=True, null=True, choices=CAUSE_OF_DEATH_CHOICES,
                                      default='unknown')

    def __str__(self) -> str:
        return f"{self.plant.name} died on {self.date_of_death.strftime('%d/%m/%Y')} due to {self.cause_of_death}"

    def __repr__(self) -> str:
        return f"PlantGraveyard(plant= {self.plant.name}({self.plant.id}), date_of_death={self.date_of_death!r}, cause_of_death={self.cause_of_death})"
