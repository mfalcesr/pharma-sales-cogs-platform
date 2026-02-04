"""
Generate synthetic daily order and return records.

Order volume per day is scaled by a monthly seasonality factor.
Approximately 3 % of orders generate a return event.
"""

import uuid
from datetime import date, timedelta

import numpy as np

from generator.config import (
    DISCOUNT_RANGE,
    MONTHLY_SEASONALITY,
    ORDERS_PER_DAY_RANGE,
    RANDOM_SEED,
    RETURN_REASONS,
    UNIT_COST_MARGIN_RANGE,
    UNITS_PER_ORDER_RANGE,
)

rng = np.random.default_rng(RANDOM_SEED + 3)


def _list_price_from_cost(unit_cost_standard: float) -> float:
    """Derive a list price by dividing the standard cost by a random margin."""
    margin = float(rng.uniform(*UNIT_COST_MARGIN_RANGE))
    return round(unit_cost_standard / margin, 2)


def generate_orders_for_date(
    target_date: date,
    products: list[dict],
    customers: list[dict],
    reps: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Generate orders and returns for a single calendar date.

    Parameters
    ----------
    target_date:
        The date for which to generate orders.
    products:
        Full product catalogue dicts.
    customers:
        Full customer list; inactive customers are filtered out internally.
    reps:
        Full sales rep list.

    Returns
    -------
    tuple[list[dict], list[dict]]
        ``(orders, returns)`` - two lists of record dicts.
    """
    active_customers = [c for c in customers if c.get("is_active", True)]
    if not active_customers:
        raise ValueError("No active customers found; cannot generate orders.")

    seasonality = MONTHLY_SEASONALITY[target_date.month]
    base_n = int(rng.integers(*ORDERS_PER_DAY_RANGE))
    n_orders = max(1, int(base_n * seasonality))

    orders: list[dict] = []
    returns: list[dict] = []

    for _ in range(n_orders):
        product = products[int(rng.integers(0, len(products)))]
        customer = active_customers[int(rng.integers(0, len(active_customers)))]
        rep = reps[int(rng.integers(0, len(reps)))]

        quantity = int(rng.integers(*UNITS_PER_ORDER_RANGE))
        list_price = _list_price_from_cost(float(product["unit_cost_standard"]))
        discount_pct = round(float(rng.uniform(*DISCOUNT_RANGE)), 6)
        net_price = round(list_price * (1.0 - discount_pct), 2)
        gross_amount = round(list_price * quantity, 2)
        net_amount = round(net_price * quantity, 2)

        order_id = str(uuid.uuid4())
        orders.append(
            {
                "order_id":     order_id,
                "order_date":   target_date.isoformat(),
                "product_id":   product["product_id"],
                "customer_id":  customer["customer_id"],
                "rep_id":       rep["rep_id"],
                "territory_id": rep["territory_id"],
                "quantity":     quantity,
                "list_price":   list_price,
                "discount_pct": discount_pct,
                "net_price":    net_price,
                "gross_amount": gross_amount,
                "net_amount":   net_amount,
            }
        )

        # ~3 % return rate
        if rng.random() < 0.03:
            days_to_return = int(rng.integers(1, 31))
            return_date = target_date + timedelta(days=days_to_return)
            qty_returned = int(rng.integers(1, quantity + 1))
            reason_idx = int(rng.integers(0, len(RETURN_REASONS)))
            returns.append(
                {
                    "return_id":         str(uuid.uuid4()),
                    "order_id":          order_id,
                    "return_date":       return_date.isoformat(),
                    "quantity_returned": qty_returned,
                    "reason":            RETURN_REASONS[reason_idx],
                }
            )

    return orders, returns
