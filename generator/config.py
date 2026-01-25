from datetime import date

RANDOM_SEED = 42

N_PRODUCTS = 20
N_REPS = 30
N_CUSTOMERS = 150
N_TERRITORIES = 10

START_DATE = date(2022, 1, 1)
END_DATE = date(2025, 12, 31)

THERAPEUTIC_AREAS = [
    "Oncology", "Cardiovascular", "Neurology",
    "Immunology", "Infectious Disease", "Endocrinology",
]

PRODUCT_LINES = ["Primary Care", "Specialty", "Biologics", "Generics"]

FORMULATIONS = [
    "Tablet", "Capsule", "Injectable", "Infusion",
    "Patch", "Inhaler", "Cream",
]

CUSTOMER_SEGMENTS = ["Hospital", "Pharmacy", "Clinic"]
CUSTOMER_TIERS = ["A", "B", "C"]

REGIONS = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]

ZONES = ["North", "South", "East", "West", "Central"]

LIST_PRICE_RANGE = (50.0, 5000.0)
DISCOUNT_RANGE = (0.05, 0.25)
UNIT_COST_MARGIN_RANGE = (0.25, 0.55)
COST_VARIANCE_PCT = 0.08

ORDERS_PER_DAY_RANGE = (20, 60)
UNITS_PER_ORDER_RANGE = (1, 500)

MONTHLY_SEASONALITY = {
    1: 0.85, 2: 0.90, 3: 1.05,
    4: 1.00, 5: 1.05, 6: 0.95,
    7: 0.90, 8: 0.85, 9: 1.10,
    10: 1.15, 11: 1.10, 12: 1.05,
}

MRR_CHURN_RATE_MONTHLY = 0.02
MRR_NEW_LOGO_RATE_MONTHLY = 0.03
MRR_EXPANSION_RATE_MONTHLY = 0.05

RETURN_REASONS = [
    "Damaged packaging", "Wrong product shipped",
    "Patient adverse reaction", "Expired stock",
    "Duplicate order", "Product recall",
]
