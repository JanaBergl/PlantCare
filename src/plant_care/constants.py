TASK_CATEGORY_CHOICES = [
    ("Watering", "watered"),
    ("Fertilizing", "fertilized"),
    ("Repotting", "repotted"),
    ("Vitamin treatment", "given vitamins"),
    ("Insecticide treatment", "treated with insecticide")
]

TASK_FREQUENCIES = {
    "Watering": 7,
    "Fertilizing": 30,
    "Repotting": 730,
    "Vitamin treatment": None,
    "Insecticide treatment": None,
}

CAUSE_OF_DEATH_CHOICES = [
    ("overwatering", "Overwatering"),
    ("underwatering", "Underwatering"),
    ("pest_infestation", "Pest Infestation"),
    ("lack_of_light", "Lack of light"),
    ("too_much_light", "Too much light"),
    ("nutrient_deficiency", "Nutrient Deficiency"),
    ("unknown", "Unknown"),
]
