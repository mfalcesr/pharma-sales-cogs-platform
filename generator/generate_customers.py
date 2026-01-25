"""
Generate synthetic pharmaceutical customer account records.

Tier distribution: A = 20 %, B = 50 %, C = 30 %.
Roughly 10 % of accounts are inactive and carry a contract_end_date.
"""

import uuid
from datetime import date, timedelta

import numpy as np
from faker import Faker

from generator.config import (
    CUSTOMER_SEGMENTS,
    CUSTOMER_TIERS,
    END_DATE,
    N_CUSTOMERS,
    RANDOM_SEED,
    REGIONS,
    START_DATE,
)

fake = Faker()
Faker.seed(RANDOM_SEED + 1)
rng = np.random.default_rng(RANDOM_SEED + 1)

# Name templates for each segment; placeholders filled at runtime
SEGMENT_NAME_TEMPLATES: dict[str, list[str]] = {
    "Hospital": [
        "{city} General Hospital",
        "{city} Medical Center",
        "St. {last} Hospital",
        "{last} Regional Medical",
    ],
    "Pharmacy": [
        "{city} Pharmacy",
        "{last} Drug Store",
        "MedPlus {city}",
        "{city} Rx",
    ],
    "Clinic": [
        "{city} Health Clinic",
        "Dr. {last} Clinic",
        "{city} Medical Associates",
        "{last} & Partners Clinic",
    ],
}


def _account_name(segment: str) -> str:
    """Generate a realistic-sounding account name for the given segment."""
    templates = SEGMENT_NAME_TEMPLATES[segment]
    template = str(rng.choice(templates))
    return template.format(city=fake.city(), last=fake.last_name())


def generate_customers(territories: list[dict]) -> list[dict]:
    """Return a list of N_CUSTOMERS customer account record dicts.

    Parameters
    ----------
    territories:
        List of territory dicts produced by ``generate_territories``.
        Used to assign each customer a valid ``territory_id``.
    """
    tier_weights = [0.20, 0.50, 0.30]  # A, B, C
    territory_ids = [t["territory_id"] for t in territories]
    total_days = (END_DATE - START_DATE).days
    customers: list[dict] = []

    for _ in range(N_CUSTOMERS):
        segment = CUSTOMER_SEGMENTS[int(rng.integers(0, len(CUSTOMER_SEGMENTS)))]
        tier = str(rng.choice(CUSTOMER_TIERS, p=tier_weights))
        region = REGIONS[int(rng.integers(0, len(REGIONS)))]
        territory_id = str(rng.choice(territory_ids))

        contract_start_offset = int(rng.integers(0, total_days // 2))
        contract_start = START_DATE + timedelta(days=contract_start_offset)

        is_active = bool(rng.random() > 0.10)
        contract_end: str | None = None
        if not is_active:
            max_end_offset = total_days - contract_start_offset
            if max_end_offset > 30:
                end_offset = int(rng.integers(30, max_end_offset))
            else:
                end_offset = 30
            contract_end = (contract_start + timedelta(days=end_offset)).isoformat()

        customers.append(
            {
                "customer_id":          str(uuid.uuid4()),
                "account_name":         _account_name(segment),
                "segment":              segment,
                "tier":                 tier,
                "region":               region,
                "territory_id":         territory_id,
                "contract_start_date":  contract_start.isoformat(),
                "contract_end_date":    contract_end or "",
                "is_active":            is_active,
            }
        )

    return customers
