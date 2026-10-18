# ADR-001: Stack tecnológico

- **Estado:** Aceptada
- **Fecha:** 2026-10-18

## Decisión

| Área | Elección |
|---|---|
| Lenguaje | Python 3.14 (misma versión en desarrollo, CI y producción) |
| Exchange | ccxt (Binance spot) |
| Datos | pandas + pyarrow (Parquet para históricos) |
| Estado y bitácora | SQLite |
| Configuración | pydantic v2 + YAML |
| CLI | typer |
| Scheduler | APScheduler (en proceso) |
| Logs | structlog (JSON) |
| Tests | pytest, pytest-cov, hypothesis, freezegun |
| Calidad | ruff, mypy (estricto en core/, risk/, execution/), pre-commit con detect-secrets |
| Desarrollo | Ubuntu 26.04 LTS, VS Code + Claude Code |
| Producción (Fase 3+) | VPS Linux en Europa con Docker (ver ADR-003) |

## Por qué Python 3.14 y no 3.12

La estación de desarrollo usa Ubuntu 26.04, cuyo Python del sistema es 3.14. Usar una sola versión en todos los entornos evita errores que solo aparecen en producción. Las dependencias centrales soportan 3.14. vectorbt (opcional, solo para notebooks) puede no soportarla; no es crítica. Plan B si una dependencia crítica falla: fijar 3.12 con `uv`.

## Consecuencias

La imagen Docker de producción usará Python 3.14. Cualquier cambio de versión requiere un nuevo ADR.
