"""
Generate monthly product cost records and MRR (Monthly Recurring Revenue) events.

Cost records:
    One row per product per calendar month.
    actual_cost = standard_cost * (1 + random variance within ±COST_VARIANCE_PCT).

MRR events:
    Tracks the revenue lifecycle for each active customer-product pair:
    new, expansion, churn, reactivation.
    State (active / churned pairs) is carried forward across months by the caller.
"""

import uuid
from datetime import date

import numpy as np

from generator.config import (
    COST_VARIANCE_PCT,
    MRR_CHURN_RATE_MONTHLY,
    MRR_EXPANSION_RATE_MONTHLY,
    RANDOM_SEED,
)

rng = np.random.default_rng(RANDOM_SEED + 4)


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------


def generate_costs_for_month(
    cost_month: date,
    products: list[dict],
) -> list[dict]:
    """Return one cost record per product for the given calendar month.

    Parameters
    ----------
    cost_month:
        Any date within the target month; the day component is normalised to 1.
    products:
        Full product catalogue dicts (must include ``product_id`` and
        ``unit_cost_standard``).
    """
    first_of_month = cost_month.replace(day=1)
    costs: list[dict] = []

    for product in products:
        standard_cost = float(product["unit_cost_standard"])
        variance = float(rng.uniform(-COST_VARIANCE_PCT, COST_VARIANCE_PCT))
        actual_cost = round(standard_cost * (1.0 + variance), 2)
        costs.append(
            {
                "cost_id":       str(uuid.uuid4()),
                "product_id":    product["product_id"],
                "cost_month":    first_of_month.isoformat(),
                "standard_cost": round(standard_cost, 2),
                "actual_cost":   actual_cost,
            }
        )

    return costs


# ---------------------------------------------------------------------------
# MRR events
# ---------------------------------------------------------------------------


def generate_mrr_events_for_month(
    event_month: date,
    customers: list[dict],
    products: list[dict],
    previous_active: set[tuple],
    previous_churned: set[tuple],
) -> tuple[list[dict], set[tuple], set[tuple]]:
    """Generate MRR lifecycle events for one calendar month.

    Parameters
    ----------
    event_month:
        Any date within the target month; the day component is normalised to 1.
    customers:
        Full customer list; inactive customers are skipped.
    products:
        Full product catalogue dicts.
    previous_active:
        Set of ``(customer_id, product_id)`` pairs that were active last month.
    previous_churned:
        Set of ``(customer_id, product_id)`` pairs that churned in a prior month
        and are eligible for reactivation.

    Returns
    -------
    tuple[list[dict], set[tuple], set[tuple]]
        ``(mrr_events, current_active, current_churned)``
    """
    events: list[dict] = []
    current_active: set[tuple] = set()
    current_churned: set[tuple] = set()

    active_customers = [c for c in customers if c.get("is_active", True)]
    first_of_month = event_month.replace(day=1)

    for customer in active_customers:
        # Each customer is associated with 1–3 randomly sampled products
        n_products = int(rng.integers(1, 4))
        sampled_products = [
            products[int(rng.integers(0, len(products)))]
            for _ in range(n_products)
        ]

        # Deduplicate in case the same product was sampled twice
        seen: set[str] = set()
        unique_products: list[dict] = []
        for p in sampled_products:
            if p["product_id"] not in seen:
                seen.add(p["product_id"])
                unique_products.append(p)

        for product in unique_products:
            pair: tuple[str, str] = (customer["customer_id"], product["product_id"])
            base_mrr = round(float(rng.uniform(1_000, 50_000)), 2)

            contract_start = date.fromisoformat(
                str(customer["contract_start_date"])
            )
            is_new = (
                contract_start.year == first_of_month.year
                and contract_start.month == first_of_month.month
            )

            if is_new:
                # Brand-new customer-product relationship this month
                events.append(
                    {
                        "event_id":    str(uuid.uuid4()),
                        "customer_id": customer["customer_id"],
                        "product_id":  product["product_id"],
                        "event_month": first_of_month.isoformat(),
                        "event_type":  "new",
                        "mrr_amount":  base_mrr,
                    }
                )
                current_active.add(pair)

            elif pair in previous_churned and rng.random() < 0.05:
                # Reactivation of a previously churned pair
                events.append(
                    {
                        "event_id":    str(uuid.uuid4()),
                        "customer_id": customer["customer_id"],
                        "product_id":  product["product_id"],
                        "event_month": first_of_month.isoformat(),
                        "event_type":  "reactivation",
                        "mrr_amount":  base_mrr,
                    }
                )
                current_active.add(pair)

            elif pair in previous_active:
                if rng.random() < MRR_CHURN_RATE_MONTHLY:
                    # Customer churned this month
                    events.append(
                        {
                            "event_id":    str(uuid.uuid4()),
                            "customer_id": customer["customer_id"],
                            "product_id":  product["product_id"],
                            "event_month": first_of_month.isoformat(),
                            "event_type":  "churn",
                            "mrr_amount":  -base_mrr,
                        }
                    )
                    current_churned.add(pair)

                elif rng.random() < MRR_EXPANSION_RATE_MONTHLY:
                    # Upsell / expansion event
                    expansion = round(
                        base_mrr * float(rng.uniform(0.05, 0.25)), 2
                    )
                    events.append(
                        {
                            "event_id":    str(uuid.uuid4()),
                            "customer_id": customer["customer_id"],
                            "product_id":  product["product_id"],
                            "event_month": first_of_month.isoformat(),
                            "event_type":  "expansion",
                            "mrr_amount":  expansion,
                        }
                    )
                    current_active.add(pair)

                else:
                    # Retained: no event emitted, pair stays active
                    current_active.add(pair)

    return events, current_active, current_churned
