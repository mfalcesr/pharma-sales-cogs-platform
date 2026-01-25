"""
Generate synthetic pharmaceutical product records.

Each product receives a UUID, a drug-sounding name whose suffix is
therapeutic-area-specific, pricing derived from a simulated list price
and cost margin, and a launch date prior to the data generation window.
"""

import uuid
from datetime import date

import numpy as np
from faker import Faker

from generator.config import (
    FORMULATIONS,
    LIST_PRICE_RANGE,
    N_PRODUCTS,
    PRODUCT_LINES,
    RANDOM_SEED,
    START_DATE,
    THERAPEUTIC_AREAS,
    UNIT_COST_MARGIN_RANGE,
)

fake = Faker()
Faker.seed(RANDOM_SEED)
rng = np.random.default_rng(RANDOM_SEED)

# Therapeutic-area-specific drug name suffixes
DRUG_SUFFIXES: dict[str, list[str]] = {
    "Oncology":           ["-mab", "-nib", "-lib"],
    "Cardiovascular":     ["-ol", "-pril", "-sartan"],
    "Neurology":          ["-pine", "-zepam", "-pam"],
    "Immunology":         ["-ab", "-umab", "-kinra"],
    "Infectious Disease": ["-mycin", "-cillin", "-vir"],
    "Endocrinology":      ["-ide", "-in", "-tide"],
}


def _drug_name(therapeutic_area: str) -> str:
    """Construct a plausible INN-style drug name for the given therapeutic area."""
    suffixes = DRUG_SUFFIXES.get(therapeutic_area, ["-ex"])
    # Strip trailing vowels from the root word for a more drug-like appearance
    root = fake.word().capitalize().rstrip("aeiou")
    suffix = str(rng.choice(suffixes))
    return root + suffix


def generate_products() -> list[dict]:
    """Return a list of N_PRODUCTS product record dicts."""
    products: list[dict] = []

    for i in range(N_PRODUCTS):
        ta = THERAPEUTIC_AREAS[i % len(THERAPEUTIC_AREAS)]
        pl = PRODUCT_LINES[int(rng.integers(0, len(PRODUCT_LINES)))]
        formulation = FORMULATIONS[int(rng.integers(0, len(FORMULATIONS)))]

        list_price = round(float(rng.uniform(*LIST_PRICE_RANGE)), 2)
        cost_margin = float(rng.uniform(*UNIT_COST_MARGIN_RANGE))
        unit_cost = round(list_price * cost_margin, 2)

        # Two-letter therapeutic area abbreviation for the product code
        ta_code = ta[:3].upper()
        product_code = f"{ta_code}-{(i + 1):03d}"

        launch_year = int(rng.integers(2015, START_DATE.year))
        launch_month = int(rng.integers(1, 13))
        # Use day 1-28 to stay valid across all months
        launch_day = int(rng.integers(1, 29))
        launch_date = date(launch_year, launch_month, launch_day)

        products.append(
            {
                "product_id":         str(uuid.uuid4()),
                "product_code":       product_code,
                "product_name":       _drug_name(ta),
                "therapeutic_area":   ta,
                "product_line":       pl,
                "formulation":        formulation,
                "launch_date":        launch_date.isoformat(),
                "unit_cost_standard": unit_cost,
            }
        )

    return products
