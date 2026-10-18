"""Configuration loading and validation with pydantic (spec CFG-01 to CFG-04).

Secrets are read only from environment variables, never from YAML.
"""

from centinela_trade.config.loader import ConfigError, load_config
from centinela_trade.config.models import (
    AppConfig,
    ExchangeConfig,
    ExecutionConfig,
    LoggingConfig,
    RiskConfig,
    SecretsConfig,
    StrategyConfig,
)

__all__ = [
    "AppConfig",
    "ConfigError",
    "ExchangeConfig",
    "ExecutionConfig",
    "LoggingConfig",
    "RiskConfig",
    "SecretsConfig",
    "StrategyConfig",
    "load_config",
]
