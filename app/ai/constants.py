DAMAGE_CLASS_ID_TO_TYPE = {
    0: "dent",
    1: "scratch",
    2: "broken_glass",
    3: "bumper_damage",
}

DAMAGE_TYPE_TO_CLASS_ID = {
    damage_type: class_id for class_id, damage_type in DAMAGE_CLASS_ID_TO_TYPE.items()
}

DAMAGE_LABELS = {
    "dent": "Dent",
    "scratch": "Scratch",
    "broken_glass": "Broken Glass",
    "bumper_damage": "Bumper Damage",
}

MODEL_STATUS_MOCK = "mock"
MODEL_STATUS_REAL = "real"
