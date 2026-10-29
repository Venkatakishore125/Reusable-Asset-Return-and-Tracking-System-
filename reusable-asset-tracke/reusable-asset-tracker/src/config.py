"""Configuration for the reusable asset tracking synthetic-data project."""
SEED = 20261022
DEFAULT_SCALE = {"assets": 20000, "shipments": 10000, "custody_events": 100000}
STARTER_SCALE = {"assets": 100, "shipments": 50, "custody_events": 500}
RETURN_WINDOW_DAYS = 14
LOSS_AFTER_DAYS = 30
