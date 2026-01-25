"""
Generate synthetic sales representative and territory records.

Territories are produced first, then each rep is assigned to one territory.
The first five reps act as regional managers; the remaining reps are assigned
one of those five as their manager.
"""

import uuid
from datetime import date, timedelta

import numpy as np
from faker import Faker

from generator.config import (
    N_REPS,
    N_TERRITORIES,
    RANDOM_SEED,
    REGIONS,
    START_DATE,
    ZONES,
)

fake = Faker()
Faker.seed(RANDOM_SEED + 2)
rng = np.random.default_rng(RANDOM_SEED + 2)


def generate_territories() -> list[dict]:
    """Return a list of N_TERRITORIES territory record dicts."""
    territories: list[dict] = []

    for i in range(N_TERRITORIES):
        region = REGIONS[i % len(REGIONS)]
        zone = ZONES[int(rng.integers(0, len(ZONES)))]
        territories.append(
            {
                "territory_id":   str(uuid.uuid4()),
                "territory_name": f"{region} Territory {i + 1}",
                "region":         region,
                "country":        "US",
                "zone":           zone,
            }
        )

    return territories


def generate_reps(territories: list[dict]) -> list[dict]:
    """Return a list of N_REPS sales rep record dicts.

    Parameters
    ----------
    territories:
        List of territory dicts produced by ``generate_territories``.
    """
    # Build five manager names that will be distributed across all reps
    manager_names = [fake.name() for _ in range(5)]
    territory_ids = [t["territory_id"] for t in territories]
    territory_regions = {t["territory_id"]: t["region"] for t in territories}

    reps: list[dict] = []

    for i in range(N_REPS):
        territory_id = str(rng.choice(territory_ids))
        region = territory_regions[territory_id]
        manager_name = manager_names[int(rng.integers(0, len(manager_names)))]

        # Hire date between 30 days and 5 years before the data window start
        days_before_start = int(rng.integers(30, 1825))
        hire_date = START_DATE - timedelta(days=days_before_start)

        annual_quota = round(float(rng.uniform(800_000, 3_000_000)), 2)

        reps.append(
            {
                "rep_id":       str(uuid.uuid4()),
                "rep_name":     fake.name(),
                "territory_id": territory_id,
                "region":       region,
                "manager_name": manager_name,
                "hire_date":    hire_date.isoformat(),
                "annual_quota": annual_quota,
            }
        )

    return reps
