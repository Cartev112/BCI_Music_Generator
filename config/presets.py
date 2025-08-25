PRESETS = {
    "consonant": {
        "weights": (1.0, 0.5, 0.8),
        "allowed_qualities": ["maj", "min", "sus2", "sus4"],
        "allow_altered": False,
        "key_filter": True,
    },
    "jazzy": {
        "weights": (1.2, 2.0, 0.8),
        "allowed_qualities": ["maj7", "m7", "7", "min"],
        "allow_altered": True,
        "key_filter": True,
    },
    "chromatic": {
        "weights": (1.5, 1.0, 2.0),
        "allowed_qualities": None,  # None => allow all
        "allow_altered": True,
        "key_filter": False,
    },
} 