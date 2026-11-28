import math

import pytest

from ohlcv_lab.aave import (
    Position,
    RateModel,
    Reserve,
    borrow_rate,
    collateral_value,
    debt_value,
    health_factor,
    liquidation_price,
    supply_rate,
    utilization,
)
from ohlcv_lab.exceptions import InvalidRiskInputError

MODEL = RateModel(base_rate=0.0, slope1=0.04, slope2=0.60, optimal_utilization=0.8, reserve_factor=0.1)


def _reserves():
    return {
        "WETH": Reserve("WETH", 2000.0, 1000.0, 500.0, 0.80, 0.825, MODEL),
        "USDC": Reserve("USDC", 1.0, 5_000_000.0, 4_000_000.0, 0.75, 0.78, MODEL),
    }


def test_utilization_is_borrowed_over_supplied():
    assert utilization(1000.0, 250.0) == 0.25


def test_utilization_of_empty_pool_is_zero():
    assert utilization(0.0, 0.0) == 0.0


def test_utilization_is_capped_at_one():
    assert utilization(100.0, 120.0) == 1.0


def test_utilization_rejects_negative_amounts():
    with pytest.raises(InvalidRiskInputError):
        utilization(-1.0, 0.0)


def test_borrow_rate_at_zero_is_base_rate():
    model = RateModel(0.01, 0.04, 0.6, 0.8, 0.1)
    assert borrow_rate(0.0, model) == 0.01


def test_borrow_rate_at_optimal_is_base_plus_slope1():
    assert borrow_rate(0.8, MODEL) == pytest.approx(0.04)


def test_borrow_rate_below_optimal_is_linear():
    assert borrow_rate(0.4, MODEL) == pytest.approx(0.02)


def test_borrow_rate_at_full_utilization_adds_slope2():
    assert borrow_rate(1.0, MODEL) == pytest.approx(0.64)


def test_borrow_rate_above_optimal_is_steeper():
    # halfway between 80 % and 100 % utilization
    assert borrow_rate(0.9, MODEL) == pytest.approx(0.04 + 0.30)


def test_borrow_rate_rejects_utilization_above_one():
    with pytest.raises(InvalidRiskInputError):
        borrow_rate(1.2, MODEL)


def test_supply_rate_is_borrow_rate_times_utilization_minus_reserve_factor():
    assert supply_rate(0.8, MODEL) == pytest.approx(0.04 * 0.8 * 0.9)


def test_rate_model_rejects_optimal_utilization_of_one():
    with pytest.raises(InvalidRiskInputError):
        RateModel(0.0, 0.04, 0.6, 1.0, 0.1)


def test_reserve_rejects_ltv_above_threshold():
    with pytest.raises(InvalidRiskInputError):
        Reserve("X", 1.0, 1.0, 0.0, 0.9, 0.8, MODEL)


def test_reserve_rejects_non_positive_price():
    with pytest.raises(InvalidRiskInputError):
        Reserve("X", 0.0, 1.0, 0.0, 0.5, 0.8, MODEL)


def test_values_in_usd():
    position = Position("a", collateral={"WETH": 10.0}, debt={"USDC": 8000.0})
    assert collateral_value(position, _reserves()) == 20_000.0
    assert debt_value(position, _reserves()) == 8000.0


def test_health_factor_uses_liquidation_threshold():
    position = Position("a", collateral={"WETH": 10.0}, debt={"USDC": 8000.0})
    # 10 * 2000 * 0.825 / 8000
    assert health_factor(position, _reserves()) == pytest.approx(2.0625)


def test_health_factor_without_debt_is_infinite():
    position = Position("a", collateral={"WETH": 1.0})
    assert math.isinf(health_factor(position, _reserves()))


def test_health_factor_with_price_override():
    position = Position("a", collateral={"WETH": 10.0}, debt={"USDC": 8000.0})
    hf = health_factor(position, _reserves(), price_overrides={"WETH": 1400.0})
    assert hf == pytest.approx(10 * 1400 * 0.825 / 8000)


def test_health_factor_unknown_symbol_raises():
    position = Position("a", collateral={"DOGE": 10.0}, debt={"USDC": 1.0})
    with pytest.raises(InvalidRiskInputError):
        health_factor(position, _reserves())


def test_liquidation_price_is_where_health_factor_hits_one():
    position = Position("a", collateral={"WETH": 10.0}, debt={"USDC": 8000.0})
    price = liquidation_price(position, _reserves(), "WETH")
    assert price == pytest.approx(8000 / (10 * 0.825))
    hf = health_factor(position, _reserves(), price_overrides={"WETH": price})
    assert hf == pytest.approx(1.0)


def test_liquidation_price_accounts_for_other_collateral():
    position = Position("a", collateral={"WETH": 5.0, "USDC": 4000.0}, debt={"USDC": 8000.0})
    price = liquidation_price(position, _reserves(), "WETH")
    hf = health_factor(position, _reserves(), price_overrides={"WETH": price})
    assert hf == pytest.approx(1.0)


def test_liquidation_price_is_zero_when_other_collateral_covers_debt():
    position = Position("a", collateral={"WETH": 1.0, "USDC": 20_000.0}, debt={"USDC": 1000.0})
    assert liquidation_price(position, _reserves(), "WETH") == 0.0


def test_liquidation_price_is_none_without_debt_or_collateral():
    reserves = _reserves()
    assert liquidation_price(Position("a", collateral={"WETH": 1.0}), reserves, "WETH") is None
    assert liquidation_price(Position("a", debt={"USDC": 1.0}), reserves, "WETH") is None
