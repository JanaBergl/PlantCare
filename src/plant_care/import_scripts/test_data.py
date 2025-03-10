import datetime
from django.utils import timezone
from plant_care.models import PlantGroup, Plant, PlantTaskFrequency, PlantCareHistory
from plant_care.constants import TASK_CATEGORY_CHOICES


def run():
    # Plant Groups
    groups = [
        {"group_name": "Herbs"},
        {"group_name": "Succulents"},
        {"group_name": "Tropical Plants"},
        {"group_name": "Cacti"}
    ]

    group_instances = []
    for group_data in groups:
        group, _ = PlantGroup.objects.get_or_create(**group_data)
        group_instances.append(group)

    # Plants
    plants = [
        {"name": "Basil", "group": group_instances[0], "date": "2024-01-15"},
        {"name": "Mint", "group": group_instances[0], "date": "2024-02-12"},
        {"name": "Aloe Vera", "group": group_instances[1], "date": "2024-03-10"},
        {"name": "Echeveria", "group": group_instances[1], "date": "2024-04-08"},
        {"name": "Monstera", "group": group_instances[2], "date": "2024-05-05"},
        {"name": "Ficus", "group": group_instances[2], "date": "2024-06-10"},
        {"name": "Opuntia Cactus", "group": group_instances[3], "date": "2024-07-15"},
        {"name": "Mammillaria Cactus", "group": group_instances[3], "date": "2024-08-20"},
        {"name": "Rosemary", "group": group_instances[0], "date": "2024-09-25"},
        {"name": "Lavender", "group": group_instances[0], "date": "2024-10-30"},
        {"name": "Sansevieria", "group": group_instances[1], "date": "2024-11-25"},
        {"name": "Hoya", "group": group_instances[1], "date": "2024-12-30"},
        {"name": "Orchid", "group": group_instances[2], "date": "2025-01-25"},
        {"name": "Philodendron", "group": group_instances[2], "date": "2025-02-28"},
        {"name": "Astrophytum", "group": group_instances[3], "date": "2025-03-10"}
    ]

    plant_instances = [Plant(**data) for data in plants]
    Plant.objects.bulk_create(plant_instances)

    # Task Frequencies
    task_frequencies = [
        {"task_type": "Watering", "frequency": 7},
        {"task_type": "Fertilizing", "frequency": 30},
        {"task_type": "Repotting", "frequency": 730},
        {"task_type": "Vitamin treatment", "frequency": None},
        {"task_type": "Insecticide treatment", "frequency": None}
    ]

    # Creating frequencies for each plant
    task_frequency_instances = []
    for plant in plant_instances:
        for task_data in task_frequencies:
            task_frequency_instances.append(PlantTaskFrequency(plant=plant, **task_data))

    PlantTaskFrequency.objects.bulk_create(task_frequency_instances)

    # Plant Care History (some entries older than the set frequency - to trigger warnings)
    history_data = [
        {"plant": plant_instances[0], "task_type": "Watering",
         "task_date": timezone.now() - datetime.timedelta(days=10)},
        {"plant": plant_instances[1], "task_type": "Watering",
         "task_date": timezone.now() - datetime.timedelta(days=5)},
        {"plant": plant_instances[2], "task_type": "Fertilizing",
         "task_date": timezone.now() - datetime.timedelta(days=40)},
        {"plant": plant_instances[3], "task_type": "Repotting",
         "task_date": timezone.now() - datetime.timedelta(days=800)},
        {"plant": plant_instances[4], "task_type": "Watering",
         "task_date": timezone.now() - datetime.timedelta(days=14)},
        {"plant": plant_instances[5], "task_type": "Vitamin treatment",
         "task_date": timezone.now() - datetime.timedelta(days=2)},
    ]

    plant_history_instances = [PlantCareHistory(**data) for data in history_data]
    PlantCareHistory.objects.bulk_create(plant_history_instances)

    print("Test data successfully added to the database.")


run()
