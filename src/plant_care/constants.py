TASK_CATEGORY_CHOICES = [
    ("W", "Watered"),
    ("F", "Fertilized"),
    ("R", "Repotted"),
    ("V", "Given vitamins"),
    ("I", "Treated with insecticide")
]

TASK_FREQUENCIES = {
    "W": 7,
    "F": 30,
    "R": 730,
    "V": None,
    "I": None,
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
