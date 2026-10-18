# Reglas para agentes de IA — `centinela-trade`

Este archivo es vinculante para cualquier agente de IA que trabaje en este repositorio (Claude Code, Codex u otros). Lo mantiene un humano; ningún agente lo modifica.

## Contexto

Este repo contiene un bot de trading de criptomonedas. Los errores aquí pueden costar dinero real. **La prudencia gana a la velocidad.**

## Objetivo común de todos los agentes

Implementar **exactamente** lo que dice `docs/spec/bot-v1.md` y medir los resultados **con honestidad**.

Tu trabajo **no** es hacer que el bot sea rentable. Un backtest con malos resultados, medido correctamente, es un éxito de ingeniería. Un backtest con buenos resultados obtenido ajustando parámetros es un fracaso, aunque se vea bien.

## Documentos de referencia (en orden de autoridad)

1. `docs/spec/bot-v1.md`: comportamiento del bot. Fuente de verdad.
2. `docs/risk_policy.md`: límites de riesgo y su justificación.
3. `docs/decisions/`: decisiones de arquitectura (ADRs).
4. `docs/backlog.md`: tareas, en orden.
5. `docs/plan.md`: plan general. Si contradice al spec, prevalece el spec.

Lee el spec y este archivo completos antes de cada tarea.

## Prohibido absolutamente

1. Leer, escribir, imprimir o registrar en logs secretos (`.env`, `*.env`, `~/.secrets`, API keys). Si encuentras un secreto expuesto, detente y repórtalo.
2. Modificar `docs/spec/`, `docs/risk_policy.md`, `config/live.yaml`, `AGENTS.md`, `CLAUDE.md` o `.claude/`.
3. Modificar `src/centinela_trade/risk/` o `src/centinela_trade/execution/` salvo que la tarea lo indique explícitamente.
4. Cambiar parámetros, umbrales, filtros o reglas de las estrategias para mejorar métricas (spec OVF-01). Si crees que una regla está mal, escríbelo en tu resumen y detente.
5. Usar el período de holdout (spec VAL-02): nunca uses `--use-holdout` ni `CENTINELA_ALLOW_HOLDOUT`.
6. Ejecutar el bot en modo `paper` o `live`, o enviar órdenes a cualquier exchange. Tú solo ejecutas tests y backtests.
7. Ejecutar tests que requieran red o credenciales. Esos tests se marcan `@pytest.mark.network`, se omiten por defecto y los ejecuta un humano.
8. Eliminar, saltar o debilitar tests, validaciones o límites para "hacer pasar" algo.
9. Agregar dependencias sin listarlas y justificarlas en el resumen de la tarea.
10. Hacer `push` a `main`, `push --force`, o fusionar ramas. Todo el trabajo va en una rama; el humano revisa y fusiona.

## Obligatorio

1. **Una tarea = una rama = un agente.** Rama `task/TNN-nombre-corto`, creada desde `main` actualizado.
2. Toda función nueva llega con tests. En `risk/` y `execution/`: 100% de cobertura de ramas.
3. `make lint` y `make test` en verde antes de declarar terminada una tarea.
4. Tipado estricto con mypy en `core/`, `risk/` y `execution/`.
5. Un cambio = una tarea. Nada de refactors oportunistas fuera del alcance.
6. Commits atómicos con formato `tipo(módulo): descripción [ID-REQ]`, donde tipo es `feat`, `fix`, `test`, `docs`, `refactor` o `chore`. Ejemplo: `feat(risk): dimensionamiento por ATR [RISK-08]`.
7. Cita los IDs de requisitos del spec (por ejemplo `MR-01`) en docstrings de las funciones que los implementan y en los nombres o docstrings de sus tests.
8. Si una instrucción contradice el spec, este archivo o la arquitectura, **detente y pregunta**.
9. Si algo del spec es ambiguo, **pregunta**. No inventes comportamiento.

## Convenciones

- **Idioma:** código, identificadores y comentarios en inglés. Documentación en `docs/` y mensajes al usuario en español.
- **Python 3.14.** Formato y lint con ruff; tipos con mypy.
- **Dinero y cantidades:** `Decimal`, nunca `float`, en `core/`, `risk/` y `execution/`.
- **Tiempo:** UTC en todo el sistema, con `datetime` timezone-aware.
- **Sin lookahead:** ninguna decisión en el instante `t` puede usar datos posteriores a `t`. Cada estrategia tiene un test que lo verifica (modificar velas posteriores a `t` no cambia la decisión en `t`).

## Al terminar cada tarea, entrega un resumen con

1. Qué se implementó, con los IDs de requisitos cubiertos.
2. Archivos creados o modificados.
3. Dependencias agregadas, con su justificación.
4. Salida resumida de `make lint` y `make test` (incluida la cobertura).
5. Dudas, supuestos tomados y riesgos que el revisor humano debe mirar.

## Arquitectura (resumen vinculante; detalle en el spec §8)

- La estrategia emite `Signal`; nunca crea órdenes ni conoce el capital.
- Toda orden pasa por `RiskManager.validate()`, sin excepción ni bypass.
- Los módulos se comunican solo mediante los tipos de `core/models.py`.
- El mismo loop corre en backtest, paper y live; solo cambia el connector.
