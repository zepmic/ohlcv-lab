"""Lending market math in the style of Aave v3: utilization, rates, health factor."""

from dataclasses import dataclass, field

from ohlcv_lab.exceptions import InvalidRiskInputError


@dataclass(frozen=True)
class RateModel:
    """Two slope interest rate model. All rates are annual, 0.04 means 4 %."""

    base_rate: float
    slope1: float
    slope2: float
    optimal_utilization: float
    reserve_factor: float

    def __post_init__(self) -> None:
        if not 0 < self.optimal_utilization < 1:
            raise InvalidRiskInputError(
                f"optimal_utilization must be between 0 and 1, got {self.optimal_utilization}"
            )
        if not 0 <= self.reserve_factor < 1:
            raise InvalidRiskInputError(
                f"reserve_factor must be in [0, 1), got {self.reserve_factor}"
            )
        for name in ("base_rate", "slope1", "slope2"):
            if getattr(self, name) < 0:
                raise InvalidRiskInputError(f"{name} must be >= 0, got {getattr(self, name)}")


@dataclass(frozen=True)
class Reserve:
    """One asset in the lending pool. Amounts are in tokens, prices in USD."""

    symbol: str
    price_usd: float
    total_supplied: float
    total_borrowed: float
    ltv: float
    liquidation_threshold: float
    rate_model: RateModel

    def __post_init__(self) -> None:
        if self.price_usd <= 0:
            raise InvalidRiskInputError(f"price_usd must be > 0, got {self.price_usd}")
        if self.total_supplied < 0 or self.total_borrowed < 0:
            raise InvalidRiskInputError("total_supplied and total_borrowed must be >= 0")
        if not 0 <= self.ltv <= self.liquidation_threshold <= 1:
            raise InvalidRiskInputError(
                "need 0 <= ltv <= liquidation_threshold <= 1, "
                f"got ltv={self.ltv}, threshold={self.liquidation_threshold}"
            )


@dataclass(frozen=True)
class Position:
    """A borrower: token amounts per symbol, collateral side and debt side."""

    user: str
    collateral: dict[str, float] = field(default_factory=dict)
    debt: dict[str, float] = field(default_factory=dict)


def utilization(total_supplied: float, total_borrowed: float) -> float:
    """Share of the supplied tokens that is currently borrowed."""
    if total_supplied < 0 or total_borrowed < 0:
        raise InvalidRiskInputError("amounts must be >= 0")
    if total_supplied == 0:
        return 0.0
    return min(total_borrowed / total_supplied, 1.0)


def borrow_rate(u: float, model: RateModel) -> float:
    """Variable borrow APR at utilization `u`.

    Below the optimal utilization the rate rises along slope1, above it
    the rate rises along the much steeper slope2.
    """
    if not 0 <= u <= 1:
        raise InvalidRiskInputError(f"utilization must be in [0, 1], got {u}")
    optimal = model.optimal_utilization
    if u <= optimal:
        return model.base_rate + model.slope1 * u / optimal
    excess = (u - optimal) / (1 - optimal)
    return model.base_rate + model.slope1 + model.slope2 * excess


def supply_rate(u: float, model: RateModel) -> float:
    """Supply APR: borrowers' interest, spread over all suppliers, minus the reserve factor."""
    return borrow_rate(u, model) * u * (1 - model.reserve_factor)


def reserve_utilization(reserve: Reserve) -> float:
    return utilization(reserve.total_supplied, reserve.total_borrowed)


def _prices(reserves: dict[str, Reserve], price_overrides: dict[str, float] | None) -> dict[str, float]:
    prices = {symbol: r.price_usd for symbol, r in reserves.items()}
    if price_overrides:
        for symbol, price in price_overrides.items():
            if price <= 0:
                raise InvalidRiskInputError(f"price for {symbol} must be > 0, got {price}")
            prices[symbol] = price
    return prices


def _lookup(reserves: dict[str, Reserve], symbol: str) -> Reserve:
    try:
        return reserves[symbol]
    except KeyError:
        raise InvalidRiskInputError(f"no reserve for symbol {symbol!r}") from None


def collateral_value(
    position: Position,
    reserves: dict[str, Reserve],
    price_overrides: dict[str, float] | None = None,
) -> float:
    """Collateral in USD, not yet weighted by the liquidation thresholds."""
    prices = _prices(reserves, price_overrides)
    for symbol in position.collateral:
        _lookup(reserves, symbol)
    return sum(amount * prices[s] for s, amount in position.collateral.items())


def debt_value(
    position: Position,
    reserves: dict[str, Reserve],
    price_overrides: dict[str, float] | None = None,
) -> float:
    """Debt in USD."""
    prices = _prices(reserves, price_overrides)
    for symbol in position.debt:
        _lookup(reserves, symbol)
    return sum(amount * prices[s] for s, amount in position.debt.items())


def weighted_collateral(
    position: Position,
    reserves: dict[str, Reserve],
    price_overrides: dict[str, float] | None = None,
) -> float:
    """Collateral in USD, each asset weighted by its liquidation threshold."""
    prices = _prices(reserves, price_overrides)
    total = 0.0
    for symbol, amount in position.collateral.items():
        reserve = _lookup(reserves, symbol)
        total += amount * prices[symbol] * reserve.liquidation_threshold
    return total


def health_factor(
    position: Position,
    reserves: dict[str, Reserve],
    price_overrides: dict[str, float] | None = None,
) -> float:
    """Threshold weighted collateral divided by debt. Below 1 the position can be liquidated.

    A position without debt has an infinite health factor.
    """
    debt = debt_value(position, reserves, price_overrides)
    if debt == 0:
        return float("inf")
    return weighted_collateral(position, reserves, price_overrides) / debt


def liquidation_price(
    position: Position,
    reserves: dict[str, Reserve],
    symbol: str,
    price_overrides: dict[str, float] | None = None,
) -> float | None:
    """Price of `symbol` at which the health factor hits 1, all other prices held fixed.

    Returns None if the position has no debt or no `symbol` collateral, and 0.0
    if the other collateral already covers the debt on its own.
    """
    amount = position.collateral.get(symbol, 0.0)
    debt = debt_value(position, reserves, price_overrides)
    if debt == 0 or amount == 0:
        return None
    reserve = _lookup(reserves, symbol)
    prices = _prices(reserves, price_overrides)
    other = weighted_collateral(position, reserves, price_overrides) - (
        amount * prices[symbol] * reserve.liquidation_threshold
    )
    needed = debt - other
    if needed <= 0:
        return 0.0
    return needed / (amount * reserve.liquidation_threshold)
