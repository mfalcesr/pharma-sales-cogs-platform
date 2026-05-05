import pytest
from datetime import date
from unittest.mock import patch


def test_generate_products_count():
    from generator.generate_products import generate_products
    from generator.config import N_PRODUCTS
    products = generate_products()
    assert len(products) == N_PRODUCTS


def test_product_fields():
    from generator.generate_products import generate_products
    products = generate_products()
    required = {"product_id", "product_code", "product_name", "therapeutic_area",
                "product_line", "formulation", "launch_date", "unit_cost_standard"}
    for p in products:
        assert required.issubset(set(p.keys()))
        assert float(p["unit_cost_standard"]) > 0


def test_generate_territories():
    from generator.generate_reps import generate_territories
    from generator.config import N_TERRITORIES
    territories = generate_territories()
    assert len(territories) == N_TERRITORIES
    ids = [t["territory_id"] for t in territories]
    assert len(ids) == len(set(ids)), "Territory IDs must be unique"


def test_generate_reps():
    from generator.generate_reps import generate_territories, generate_reps
    from generator.config import N_REPS
    territories = generate_territories()
    reps = generate_reps(territories)
    assert len(reps) == N_REPS
    territory_ids = {t["territory_id"] for t in territories}
    for rep in reps:
        assert rep["territory_id"] in territory_ids
        assert float(rep["annual_quota"]) > 0


def test_generate_customers():
    from generator.generate_reps import generate_territories
    from generator.generate_customers import generate_customers
    from generator.config import N_CUSTOMERS, CUSTOMER_SEGMENTS, CUSTOMER_TIERS
    territories = generate_territories()
    customers = generate_customers(territories)
    assert len(customers) == N_CUSTOMERS
    for c in customers:
        assert c["segment"] in CUSTOMER_SEGMENTS
        assert c["tier"] in CUSTOMER_TIERS


def test_generate_orders_for_date():
    from generator.generate_products import generate_products
    from generator.generate_reps import generate_territories, generate_reps
    from generator.generate_customers import generate_customers
    from generator.generate_orders import generate_orders_for_date
    territories = generate_territories()
    products = generate_products()
    customers = generate_customers(territories)
    reps = generate_reps(territories)
    orders, returns = generate_orders_for_date(date(2024, 3, 15), products, customers, reps)
    assert len(orders) > 0
    for o in orders:
        assert o["net_amount"] <= o["gross_amount"]
        assert 0 < o["discount_pct"] < 1
    # Returns should reference valid order IDs
    order_ids = {o["order_id"] for o in orders}
    for r in returns:
        assert r["order_id"] in order_ids


def test_generate_costs_for_month():
    from generator.generate_products import generate_products
    from generator.generate_costs import generate_costs_for_month
    products = generate_products()
    costs = generate_costs_for_month(date(2024, 1, 1), products)
    assert len(costs) == len(products)
    for c in costs:
        assert c["actual_cost"] > 0
        assert c["standard_cost"] > 0
