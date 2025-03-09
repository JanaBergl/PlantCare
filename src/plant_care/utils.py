import datetime

from django.core.exceptions import ValidationError
from plant_care.constants import TASK_CATEGORY_CHOICES
from plant_care.models import PlantCareHistory, Plant


def show_care_warnings() -> list:
    """
    Checks if a plant needs care based on their set task frequency and last log in PlantCareHistory
    """
    today = datetime.date.today()
    overdue_tasks = []

    plants = Plant.objects.filter(is_alive=True)
    for plant in plants:
        for task_type, task_type_display in TASK_CATEGORY_CHOICES:
            care_frequency = plant.task_frequencies.filter(task_type=task_type).first()

            if care_frequency is None or care_frequency.frequency is None:
                continue

            days_allowed = care_frequency.frequency

            last_log = PlantCareHistory.objects.filter(plant=plant, task_type=task_type).order_by('-task_date').first()
            if last_log:
                days_since_task = (today - last_log.task_date.date()).days

                if days_since_task >= days_allowed:
                    overdue_tasks.append({
                        "plant": plant,
                        "group": plant.group,
                        "task_type": task_type,
                        "days_since_task": days_since_task,
                    })

    return overdue_tasks


def is_member_of_group(user, group_names):
    """Otestujeme clenstvi uzivatele ve skupinach, pokud je clenem alespon jedne z nich
    vrati to True jinak False

    group_names = str, [name1, name2,....]
    """
    if isinstance(group_names, str):
        rights_exist = user.groups.filter(name=group_names).exists()
    else:
        rights_exist = user.groups.filter(name__in=group_names).exists()
    return rights_exist
