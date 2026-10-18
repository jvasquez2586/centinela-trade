"""Configuration loading: ``base.yaml`` + environment override + secrets (spec CFG-01).

The effective configuration is ``config/base.yaml`` deep-merged with
``config/<env>.yaml``; secrets come only from environment variables. Any problem
(missing file, malformed YAML, duplicate key, secret in YAML, missing or
out-of-range value) raises ``ConfigError`` so the bot does not start.
"""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, get_args

import yaml
from pydantic import ValidationError

from centinela_trade.config.models import AppConfig, Environment, SecretsConfig

DEFAULT_CONFIG_DIR = Path("config")
BASE_FILE = "base.yaml"

ENVIRONMENTS: tuple[str, ...] = get_args(Environment)

#: ``SecretsConfig`` field -> environment variable it is read from: the field name in
#: upper case, as listed in ``.env.example``.
SECRET_ENV_VARS: dict[str, str] = {field: field.upper() for field in SecretsConfig.model_fields}

# Key names that look like credentials (same heuristic as spec LOG-04).
_SECRET_KEY_MARKERS = ("key", "secret", "token", "password")


class ConfigError(ValueError):
    """The configuration is missing, malformed or outside the allowed ranges."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys instead of keeping the last one."""


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_config(
    env: str,
    config_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> AppConfig:
    """Load and validate the effective configuration for ``env`` (spec CFG-01, CFG-02).

    Args:
        env: ``backtest``, ``paper`` or ``live``.
        config_dir: directory holding ``base.yaml`` and ``<env>.yaml``; defaults to
            ``./config``.
        environ: source of secrets; defaults to ``os.environ``.

    Raises:
        ConfigError: if anything is missing, malformed or out of range.
    """
    if env not in ENVIRONMENTS:
        raise ConfigError(f"unknown environment {env!r}; expected one of {list(ENVIRONMENTS)}")
    directory = DEFAULT_CONFIG_DIR if config_dir is None else config_dir

    base = _read_yaml(directory / BASE_FILE)
    override = _read_yaml(directory / f"{env}.yaml")
    declared = override.get("environment")
    if declared != env:
        raise ConfigError(
            f"{directory / f'{env}.yaml'} must declare 'environment: {env}' (found {declared!r})"
        )

    merged = _deep_merge(base, override)
    merged["secrets"] = _read_secrets(os.environ if environ is None else environ)
    try:
        return AppConfig.model_validate(merged)
    except ValidationError as exc:
        raise ConfigError(f"invalid configuration for environment {env!r}:\n{exc}") from exc


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    try:
        # _UniqueKeyLoader is a SafeLoader: no arbitrary Python objects are built.
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    _reject_secrets(data, path)
    return data


def _reject_secrets(data: Mapping[Any, Any], path: Path, prefix: str = "") -> None:
    """Secrets are read only from environment variables, never from YAML."""
    for key, value in data.items():
        dotted = f"{prefix}{key}"
        if any(marker in str(key).lower() for marker in _SECRET_KEY_MARKERS):
            raise ConfigError(
                f"{path}: key {dotted!r} looks like a secret; secrets must come from "
                "environment variables, never from YAML"
            )
        if isinstance(value, Mapping):
            _reject_secrets(value, path, prefix=f"{dotted}.")


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``override`` into ``base``: nested mappings merge, anything else replaces."""
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _read_secrets(environ: Mapping[str, str]) -> SecretsConfig:
    """Read credentials from ``environ``; empty variables count as unset."""
    values = {field: environ.get(var) or None for field, var in SECRET_ENV_VARS.items()}
    return SecretsConfig.model_validate(values)
