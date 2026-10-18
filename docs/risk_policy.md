# Política de riesgo — v1

- **Fecha:** 2026-10-18
- **Autoridad:** fuente de verdad de los valores de riesgo, junto con `docs/spec/bot-v1.md` §4. Solo la modifica un humano.

## Principio

El riesgo se controla en una capa independiente (el RiskManager) que la estrategia no puede saltarse. Ninguna señal, por buena que parezca, justifica exceder un límite.

## Límites y justificación

| Límite | Valor | Justificación |
|---|---|---|
| Riesgo por operación | 1% | Con 5 pérdidas seguidas (breaker CB-02) la pérdida acumulada es ~5%, lejos del drawdown máximo. |
| Tamaño máximo de posición | 25% | Limita la exposición a un hueco de precio mayor que el stop. |
| Posiciones simultáneas | 1 | Simplicidad y reconciliación trivial en v1. |
| Pérdida diaria | 3% | Evita que un día anómalo encadene pérdidas. |
| Drawdown: alerta / apagado | 10% / 15% | Margen para revisar antes del apagado; 15% es el máximo tolerable para capital de aprendizaje. |
| Órdenes por hora | 6 | Una estrategia de 1h/4h nunca lo necesita: superarlo es un bug. |
| Pérdidas consecutivas | 5 | Señal de cambio de régimen o de fallo; obliga a revisar. |
| Stop loss | 2 × ATR(14) | Se adapta a la volatilidad; el riesgo en USD se mantiene constante vía tamaño. |
| Capital live inicial | 100 USD | Pérdida total aceptable como costo de aprendizaje. |

## Escalamiento de capital

Ver spec ESC-01 a ESC-03: por evidencia (≥ 20 operaciones por nivel, sin incidentes, slippage < 2× el asumido), como máximo duplicando, decidido por un humano.

## Quién puede cambiar qué

- Valores en `config/backtest.yaml` y `config/paper.yaml`: un humano, o un agente con instrucción explícita, siempre dentro de los topes duros (spec CFG-02).
- `config/live.yaml`, este documento y los topes duros del código: **solo un humano**, con un ADR que explique el cambio.
