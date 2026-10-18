"""Typed, immutable configuration models (spec CFG-01, CFG-02, CFG-03).

Every field is required: values live in ``config/*.yaml``, never as defaults in the
code (CFG-01). The hard caps of CFG-02 are enforced here, so an out-of-range value
stops the bot before it starts.

Money and percentages are ``Decimal`` because ``risk/`` and ``execution/`` consume
them (AGENTS.md conventions). Counters are strict integers: ``True`` or ``2.5`` are
rejected instead of being silently coerced.
"""

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictInt, model_validator

Environment = Literal["backtest", "paper", "live"]

#: CFG-02: ``max_capital_usd`` upper cap, applied only in the ``live`` environment.
LIVE_MAX_CAPITAL_USD = Decimal(1000)


class _FrozenModel(BaseModel):
    """Base for config models: immutable and rejecting unknown keys (CFG-03 schema)."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ExchangeConfig(_FrozenModel):
    """Exchange and instrument. v1 scope is Binance spot, BTC/USDT only (spec §2)."""

    name: Literal["binance"]
    market: Literal["spot"]
    symbol: Literal["BTC/USDT"]
    account_label: str | None = Field(min_length=1)


class StrategyConfig(_FrozenModel):
    """Selected strategy and timeframe (spec §2, §6.5).

    Both are ``None`` until the backtest decides (ADR-002); ``live`` refuses to load
    while they are ``None`` (see ``AppConfig``). Strategy parameters are not
    configurable here: they belong to the versioned strategy (STR-06, OVF-01).
    """

    name: Literal["mean_reversion", "trend_following"] | None
    timeframe: Literal["1h", "4h"] | None


class RiskConfig(_FrozenModel):
    """Risk limits. Keys are exactly those of ``config/live.yaml`` (CFG-03).

    Ranges marked CFG-02 are the hard caps of the spec. The remaining keys have no
    cap in CFG-02, so they are only required to be positive.
    """

    # CFG-02: > 0 everywhere; <= 1000 in live only (enforced by AppConfig).
    max_capital_usd: Decimal = Field(gt=0)
    # RISK-01 / CFG-02: > 0 and <= 2.
    risk_per_trade_pct: Decimal = Field(gt=0, le=2)
    # RISK-02 / CFG-02: > 0 and <= 50.
    max_position_pct: Decimal = Field(gt=0, le=50)
    # RISK-03 / CFG-02: exactly 1 in v1.
    max_open_positions: StrictInt = Field(ge=1, le=1)
    # RISK-04 / CFG-02: > 0 and <= 5.
    daily_loss_limit_pct: Decimal = Field(gt=0, le=5)
    # RISK-05 / CFG-02: > 0 and < max_drawdown_pct (checked below).
    drawdown_alert_pct: Decimal = Field(gt=0)
    # RISK-06 / CB-01 / CFG-02: > 0 and <= 25.
    max_drawdown_pct: Decimal = Field(gt=0, le=25)
    # RISK-07 / CB-07 / CFG-02: >= 1 and <= 12.
    max_orders_per_hour: StrictInt = Field(ge=1, le=12)
    # CB-02 / CFG-02: >= 2 and <= 10.
    max_consecutive_losses: StrictInt = Field(ge=2, le=10)
    # CB-04.
    max_consecutive_api_errors: StrictInt = Field(ge=1)
    max_disconnect_minutes_with_position: StrictInt = Field(ge=1)
    # CB-05.
    slippage_breaker_multiplier: Decimal = Field(gt=0)
    slippage_breaker_trades: StrictInt = Field(ge=1)
    # CB-06.
    volatility_pause_pct_1h: Decimal = Field(gt=0)
    # RISK-10: price within +/- price_band_pct of the last price.
    price_band_pct: Decimal = Field(gt=0)
    # RISK-09: stop distance range (checked below).
    min_stop_distance_pct: Decimal = Field(gt=0)
    max_stop_distance_pct: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def _check_cross_field_limits(self) -> Self:
        """CFG-02: drawdown alert below the shutdown level; RISK-09: a non-empty range."""
        if self.drawdown_alert_pct >= self.max_drawdown_pct:
            raise ValueError(
                f"drawdown_alert_pct ({self.drawdown_alert_pct}) must be lower than "
                f"max_drawdown_pct ({self.max_drawdown_pct}) (spec CFG-02)"
            )
        if self.min_stop_distance_pct >= self.max_stop_distance_pct:
            raise ValueError(
                f"min_stop_distance_pct ({self.min_stop_distance_pct}) must be lower than "
                f"max_stop_distance_pct ({self.max_stop_distance_pct}) (spec RISK-09)"
            )
        return self


class ExecutionConfig(_FrozenModel):
    """Order execution settings (spec EXE-01, EXE-02, EXE-07)."""

    order_type: Literal["market"]
    stop_limit_buffer_pct: Decimal = Field(gt=0)
    reconciliation_interval_minutes: StrictInt = Field(ge=1)


class LoggingConfig(_FrozenModel):
    """Structured logging settings (spec LOG-04; wired up in task T12)."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_dir: str = Field(min_length=1)


class SecretsConfig(_FrozenModel):
    """Credentials, read only from environment variables, never from YAML.

    All are optional at load time: backtests need none, and the components that need
    one (connectors, alerts) must check for it. Excluded from ``config_hash`` (CFG-04).
    """

    binance_testnet_api_key: SecretStr | None = None
    binance_testnet_api_secret: SecretStr | None = None
    binance_demo_api_key: SecretStr | None = None
    binance_demo_api_secret: SecretStr | None = None
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: SecretStr | None = None


class AppConfig(_FrozenModel):
    """Effective configuration of one run: ``base.yaml`` + environment override + env vars."""

    environment: Environment
    exchange: ExchangeConfig
    strategy: StrategyConfig
    risk: RiskConfig
    execution: ExecutionConfig
    logging: LoggingConfig
    secrets: SecretsConfig = Field(default_factory=SecretsConfig, exclude=True, repr=False)

    @model_validator(mode="after")
    def _check_live_requirements(self) -> Self:
        """Live refuses to start without a chosen strategy or above the capital cap."""
        if self.environment != "live":
            return self
        if self.strategy.name is None or self.strategy.timeframe is None:
            raise ValueError(
                "live requires strategy.name and strategy.timeframe; they stay null until "
                "the backtest result is decided (ADR-002) and a human edits config/live.yaml"
            )
        if self.risk.max_capital_usd > LIVE_MAX_CAPITAL_USD:
            raise ValueError(
                f"risk.max_capital_usd ({self.risk.max_capital_usd}) must be <= "
                f"{LIVE_MAX_CAPITAL_USD} in live (spec CFG-02)"
            )
        return self
