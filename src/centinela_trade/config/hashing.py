"""Configuration fingerprint recorded in every journal row (spec CFG-04, LOG-02)."""

import hashlib
import json
from decimal import Decimal
from typing import Any

from centinela_trade.config.models import AppConfig


def config_hash(config: AppConfig) -> str:
    """SHA-256 of the normalized effective configuration, without secrets (spec CFG-04).

    Normalization makes the hash independent of YAML key order and of how a number
    is written (``1``, ``1.0`` and ``1.00`` hash the same).
    """
    data = config.model_dump(mode="python", exclude={"secrets"})
    canonical = json.dumps(
        _normalize(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return value
