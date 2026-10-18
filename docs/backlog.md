# Backlog — Sprints 0 y 1

Reemplaza a los prompts P1-P10 de `docs/plan.md` §12, adaptados al spec v1. Las tareas se ejecutan **en orden**, una por rama, cada una revisada por un humano antes de la siguiente.

## Plantilla de prompt para cada tarea

```
Lee completos AGENTS.md y docs/spec/bot-v1.md.
Ejecuta la tarea TNN de docs/backlog.md.
Crea la rama task/TNN-<nombre-corto> desde main actualizado.
Respeta las restricciones y criterios de aceptación de la tarea.
Si algo es ambiguo o contradice el spec, detente y pregunta antes de implementar.
Al terminar, entrega el resumen que exige AGENTS.md. No hagas push.
```

Marca de revisión: 🔴 revisión humana línea por línea + revisión adversarial de un segundo agente ("encuentra cómo este código podría perder dinero"). 🟡 revisión humana del diff completo.

---

## Sprint 0 — Fundaciones

### T01 — Estructura del repositorio 🟡
- **Tarea:** estructura de carpetas de `docs/plan.md` §7 (sin `dashboard/`), con el paquete `src/centinela_trade/` en lugar de `src/tradebot/`, y agregando `src/centinela_trade/journal/` (spec §7). Punto de entrada de consola `centinela` en `pyproject.toml` (nombre del proyecto: `centinela-trade`). `pyproject.toml` para Python 3.14 con dependencias: ccxt, pandas, pyarrow, pydantic>=2, structlog, typer, apscheduler; dev: pytest, pytest-cov, hypothesis, freezegun, ruff, mypy, pre-commit. `Makefile` con `setup`, `lint`, `test`, `format`. Pre-commit con ruff y detect-secrets. `.env.example` con claves vacías: `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`, `BINANCE_DEMO_API_KEY`, `BINANCE_DEMO_API_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. README breve. Paquetes vacíos con `__init__.py` y docstring de propósito. Configurar el marcador `network` de pytest para que se omita por defecto.
- **Restricciones:** sin lógica de negocio. No tocar archivos existentes (`AGENTS.md`, `CLAUDE.md`, `.claude/`, `docs/`, `config/live.yaml`, `.gitignore` salvo agregar entradas).
- **Aceptación:** `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` funciona; `make lint` y `make test` pasan con al menos un test placeholder.

### T02 — Configuración 🟡
- **Tarea:** modelos pydantic v2 en `src/centinela_trade/config/`: `AppConfig`, `ExchangeConfig`, `StrategyConfig`, `RiskConfig`, `ExecutionConfig`, `LoggingConfig`. Las claves de `RiskConfig` son exactamente las de `config/live.yaml`. Carga: `config/base.yaml` + override por entorno (`backtest`, `paper`, `live`) + secretos solo desde variables de entorno. `load_config(env) -> AppConfig`. Cálculo de `config_hash` (CFG-04). Crear `base.yaml`, `backtest.yaml` y `paper.yaml`.
- **Requisitos:** CFG-01, CFG-02 (topes duros), CFG-04.
- **Restricciones:** no modificar `config/live.yaml`. Los secretos nunca se leen desde YAML.
- **Aceptación:** tests de carga por entorno; errores claros ante campos faltantes o fuera de rango (un test por cada tope de CFG-02); `load_config("live")` falla con mensaje claro mientras `strategy.name` sea `null`; el hash no cambia si se reordena el YAML y no incluye secretos.

### T03 — Modelos y contratos 🔴
- **Tarea:** `core/models.py` con los tipos de ARQ-03 y `core/interfaces.py` con las interfaces de ARQ-04. `core/exceptions.py`.
- **Requisitos:** ARQ-03, ARQ-04, ALC-01, STR-03, STR-04.
- **Restricciones:** son los contratos de todo el sistema. Solo tipos, validaciones y docstrings; sin lógica de negocio.
- **Aceptación:** mypy estricto sin errores; tests de inmutabilidad y de validaciones (por ejemplo, cantidades negativas rechazadas, timestamps sin zona horaria rechazados).

## Sprint 1 — Ciclo completo en backtest y dry-run

### T04 — Datos: descarga, almacenamiento y calidad 🟡
- **Tarea:** `data/collector.py` (OHLCV de Binance spot vía ccxt, endpoints públicos, paginación, reintentos exponenciales, respeto de rate limits), `data/storage.py` (Parquet particionado por par/timeframe/año en `data/raw/`), `data/validation.py` (VAL-01). Guardia de holdout en el cargador (VAL-02). Script `scripts/download_history.py` para 4 años de BTC/USDT en 1h, 4h y 1d.
- **Aceptación:** tests con respuestas de ccxt simuladas: paginación, detección de huecos, idempotencia (descargar dos veces no duplica), y que el cargador rechace el período de holdout sin la doble autorización.

### T05 — Indicadores 🟡
- **Tarea:** `strategies/indicators.py` con las definiciones exactas de spec §3.4 y la etiqueta de régimen REG-01.
- **Aceptación:** tests contra valores calculados a mano en series pequeñas; IND-01 (calentamiento); test anti-lookahead por indicador.

### T06 — Estrategias A y B 🔴
- **Tarea:** `strategies/base.py`, `strategies/mean_reversion.py`, `strategies/trend_following.py`.
- **Requisitos:** STR-01 a STR-06, MR-01, MR-02, TF-01, TF-02, parámetros de §3.6.
- **Aceptación:** con velas sintéticas: señal de entrada en el escenario esperado para cada estrategia; sin señal bajo la SMA(200) diaria; cada motivo de salida probado; uso correcto de la vela diaria **completa** (STR-02); test anti-lookahead.

### T07 — Gestor de riesgo y circuit breakers 🔴
- **Tarea:** `risk/manager.py`, `risk/limits.py`, `risk/circuit_breakers.py`.
- **Requisitos:** RISK-01 a RISK-11, CB-01 a CB-09.
- **Aceptación:** 100% de cobertura de ramas; property tests con hypothesis: para cualquier entrada, una orden aprobada nunca excede ningún límite, y con un breaker abierto nada se aprueba; persistencia del breaker tras reinicio simulado.

### T08 — Bitácora 🟡
- **Tarea:** `journal/` con el esquema de spec §7 en SQLite, migraciones simples y una API de escritura usada por estrategia, riesgo y ejecución.
- **Requisitos:** LOG-01 a LOG-03.
- **Aceptación:** tests de que las tablas son de solo inserción (la API no expone update/delete); un ciclo simulado deja filas correlacionadas en todas las tablas; consultas de ejemplo en `docs/journal_queries.md`.

### T09 — Connector de backtest 🔴
- **Tarea:** `connectors/base.py` y `connectors/backtest.py`.
- **Requisitos:** ARQ-05, VAL-04, VAL-05, EXE-02 (simulación del stop).
- **Aceptación:** tests con valores exactos de fills, comisiones y slippage; stop con y sin hueco de apertura; stop y objetivo en la misma vela → stop primero; saldo nunca negativo.

### T10 — Motor de ejecución 🔴
- **Tarea:** `execution/engine.py` y `execution/order_state.py`.
- **Requisitos:** EXE-01 a EXE-07.
- **Aceptación:** 100% de cobertura de ramas; transiciones inválidas lanzan excepción; idempotencia; secuencia de salida EXE-04 incluido el caso de stop ya ejecutado; fallo del connector a mitad de operación no deja estado inconsistente.

### T11 — Motor de backtest, métricas y reporte 🟡
- **Tarea:** `backtesting/engine.py` (loop vela a vela con los módulos de producción), `metrics.py` (VAL-07), `sensitivity.py` (VAL-08), `report.py` (markdown + curvas de equity y drawdown en `data/reports/<timestamp>/`, con config, `config_hash` y commit de git), comparación de las 4 combinaciones según §6.5, y métricas por ventana y régimen (VAL-03).
- **Aceptación:** test de paridad (VAL-06); test con una estrategia trivial de resultado conocido a mano; el reporte indica qué combinaciones califican y por qué.

### T12 — Logging estructurado 🟡
- **Tarea:** `logging/setup.py` según LOG-04, integrado en todos los módulos.
- **Aceptación:** un ciclo completo produce la cadena de eventos correlacionados; un secreto pasado por error queda redactado.

### T13 — CLI e integración 🟡
- **Tarea:** `cli.py` con typer, expuesto como comando `centinela`: `collect`, `backtest`, `run --mode dry-run`, `report`, `breaker status`, `breaker close` (confirmación interactiva). `run --mode live` y `run --mode paper` se rechazan con mensaje explícito en este sprint.
- **Aceptación:** test end-to-end con velas sintéticas; la bitácora muestra la cadena completa; README actualizado con el flujo de uso.

---

## Después del Sprint 1 (no ejecutar todavía)

- Ejecutar el backtest completo y redactar `docs/decisions/002-resultado-backtest.md` (humano).
- Connector `paper` y `live_ccxt` apuntado a Demo Mode; alertas Telegram; reconciliación; kill switch (Fase 3).
