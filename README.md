# Centinela Trade

Bot de trading de BTC/USDT en Binance spot: solo compras, sin apalancamiento, una posición a la vez.

- Comportamiento del bot: [`docs/spec/bot-v1.md`](docs/spec/bot-v1.md) (fuente de verdad).
- Política de riesgo: [`docs/risk_policy.md`](docs/risk_policy.md).
- Reglas para agentes de IA: [`AGENTS.md`](AGENTS.md).
- Tareas: [`docs/backlog.md`](docs/backlog.md).

> Nada en este repositorio es asesoría financiera. El trading algorítmico tiene alta probabilidad de pérdida de capital.

**Estado:** Sprint 0. Estructura y herramientas; todavía sin lógica de negocio.

## Requisitos

- Python 3.14 (ver ADR-001).
- `make`.

## Instalación

```bash
make setup        # crea .venv, instala el paquete con extras [dev] y los hooks de pre-commit
cp .env.example .env   # solo si vas a usar credenciales; .env nunca se versiona
```

## Comandos

| Comando | Qué hace |
|---|---|
| `make setup` | Crea el entorno virtual e instala dependencias y hooks de pre-commit |
| `make lint` | `ruff check`, `ruff format --check` y `mypy` |
| `make test` | `pytest` con cobertura de ramas |
| `make format` | Aplica correcciones de ruff y formatea el código |
| `.venv/bin/centinela --help` | Comando de terminal del bot (se completa en la tarea T13) |

Los tests marcados `@pytest.mark.network` necesitan red o credenciales: se omiten por defecto y solo los ejecuta un humano con `.venv/bin/pytest --run-network`.

## Estructura

```
src/centinela_trade/
├── core/          # modelos, interfaces y excepciones (contratos)
├── config/        # carga y validación de configuración
├── data/          # descarga, almacenamiento y calidad de datos históricos
├── strategies/    # estrategias e indicadores
├── risk/          # gestor de riesgo y circuit breakers
├── execution/     # motor de ejecución y estados de órdenes
├── connectors/    # backtest, paper y live
├── backtesting/   # motor de backtest, métricas y reportes
├── journal/       # bitácora de decisiones en SQLite
├── monitoring/    # reportes y alertas
├── logging/       # logs estructurados JSON
└── cli.py         # comando `centinela`
tests/             # unit/, integration/, fixtures/
scripts/           # scripts de soporte
notebooks/         # análisis exploratorio; nunca importado por src/
infra/             # despliegue (fases posteriores)
config/            # configuración YAML por entorno
docs/              # spec, política de riesgo, ADRs, backlog y plan
```
