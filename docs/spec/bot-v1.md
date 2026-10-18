# Especificación del Bot v1 — Centinela Trade (`centinela-trade`)

- **Versión:** 1.0
- **Estado:** Aprobada por el responsable del proyecto, 2026-10-18
- **Autoridad:** este documento es la **fuente de verdad** del comportamiento del bot. Si contradice a `docs/plan.md`, prevalece este documento. Si contradice al código, el código está mal.
- **Cambios:** solo los hace un humano, y cada cambio se registra en el historial al final. Ningún agente de IA modifica este archivo.

---

## 0. Cómo deben usar este documento los agentes de IA

1. Lee este documento y `AGENTS.md` completos antes de cualquier tarea.
2. Implementa exactamente lo especificado. Si algo es ambiguo, **detente y pregunta**: no inventes comportamiento.
3. Los valores numéricos de este documento son **parámetros de libro, no optimizados**. Está prohibido cambiarlos para mejorar resultados de backtest (ver §6.7).
4. Cada requisito tiene un identificador (por ejemplo, `RISK-03`). Cítalo en commits, tests y resúmenes de tareas.

---

## 1. Objetivo y definición de éxito

**OBJ-01. Objetivo:** obtener rentabilidad neta positiva y sostenida operando BTC/USDT, con pérdidas acotadas. "Neta" significa después de comisiones y slippage.

**OBJ-02. Métrica de validación** (decide si el bot avanza de fase): expectativa neta por operación positiva, medida en datos fuera de muestra (out-of-sample).

```
expectativa_neta = promedio(pnl_neto_usd de cada operación)
                 = tasa_acierto × ganancia_media − (1 − tasa_acierto) × pérdida_media − costos
```

**OBJ-03. Métrica de seguimiento** (reporte automático semanal, corte lunes 00:00 UTC): P&L neto semanal en USD y %, número de operaciones, tasa de acierto, drawdown actual y máximo de la semana.

**OBJ-04. Veredicto periódico:** retorno neto acumulado en ventanas móviles de 12 semanas, comparado contra (a) mantener BTC (buy & hold) y (b) no operar (USDT).

**OBJ-05. Restricción no negociable:** drawdown máximo de 15% del capital asignado. Superarlo apaga el bot aunque el retorno acumulado sea positivo.

**OBJ-06. Lo que NO es un objetivo:** la tasa de acierto alta, el número de operaciones, ni una meta fija de % semanal. Ninguna de estas debe perseguirse por sí misma.

---

## 2. Alcance

**Dentro del alcance v1:**

| Dimensión | Valor |
|---|---|
| Exchange | Binance spot (ver ADR-003) |
| Par | BTC/USDT |
| Dirección | Solo compras (long only) |
| Posiciones simultáneas | 1 |
| Temporalidades evaluadas | 1h y 4h (configurable); la definitiva se elige en backtest (§6.5) |
| Estrategias evaluadas | A: reversión a la media, B: seguimiento de tendencia (§3) |
| Apalancamiento | Ninguno |
| Capital live inicial | 100 USD, con escalamiento por evidencia (§4.6) |

**Fuera del alcance v1** (requieren una nueva versión de este spec): ventas en corto, margen, futuros, apalancamiento, otros pares, varias estrategias en vivo al mismo tiempo, multi-exchange, machine learning, agentes de IA dentro del loop de trading, interfaz web, pago de comisiones con BNB.

**ALC-01.** El modelo `Signal` incluye el campo `side` desde el inicio, para que una futura v2 con cortos no obligue a reescribir contratos.

---

## 3. Estrategias

### 3.1 Reglas comunes a ambas estrategias

- **STR-01.** Las señales se evalúan solo al **cierre** de cada vela. Nunca se usa información de una vela en curso ni posterior (prohibido el lookahead).
- **STR-02. Filtro de régimen diario (común a A y B):** solo se permiten entradas si el cierre de la **última vela diaria completa** (día UTC cerrado antes o en el instante de cierre de la vela evaluada) es mayor que la SMA(200) de los cierres diarios hasta esa misma vela.
- **STR-03.** La estrategia **no conoce** el capital, el tamaño de la posición ni las órdenes. Solo recibe velas y su propio estado (si está en posición, precio y vela de entrada) y emite `Signal`.
- **STR-04.** Cada `Signal` de entrada incluye un `stop_price` propuesto y un `reason` legible en una línea.
- **STR-05. Stop loss (ambas estrategias):** `stop_price = precio_de_referencia − 2 × ATR(14)`, donde el ATR es el de la temporalidad operada en la vela de la señal. En backtest, el precio de referencia es el de llenado de la entrada; en paper/live, el precio real de llenado.
- **STR-06.** Cada estrategia tiene un atributo `version` (semver). Cualquier cambio de lógica o de parámetros por defecto incrementa la versión.

### 3.2 Estrategia A — reversión a la media (`mean_reversion`)

**Hipótesis:** tras una caída brusca fuera de su rango habitual, en un mercado no bajista, el precio tiende a volver a su media.

- **MR-01. Entrada (compra):** se cumplen las tres condiciones en la vela cerrada:
  1. `close < bollinger_lower(20, 2.0)`
  2. `RSI(14) < 30`
  3. filtro de régimen STR-02 verdadero
- **MR-02. Salida**, lo que ocurra primero:
  1. **Objetivo:** `close >= bollinger_middle(20)` → señal de salida `TARGET`.
  2. **Stop loss:** según STR-05, ejecutado por la orden en el exchange → `STOP`.
  3. **Tiempo:** 48 velas desde la entrada sin resolución → señal de salida `TIME`.

### 3.3 Estrategia B — seguimiento de tendencia (`trend_following`)

**Hipótesis:** una ruptura al alza con tendencia confirmada tiende a continuar.

- **TF-01. Entrada (compra):** se cumplen las tres condiciones en la vela cerrada:
  1. `close > máximo(high)` de las **20 velas anteriores** (sin incluir la vela actual)
  2. `ADX(14) > 20`
  3. filtro de régimen STR-02 verdadero
- **TF-02. Salida**, lo que ocurra primero:
  1. **Agotamiento:** `close < mínimo(low)` de las **10 velas anteriores** (sin incluir la actual) → `TREND_EXIT`.
  2. **Stop loss:** según STR-05 → `STOP`.

### 3.4 Definiciones exactas de indicadores

Se implementan con pandas puro (sin TA-Lib), en `strategies/indicators.py`, con tests contra valores calculados a mano o de referencia publicada.

| Indicador | Definición |
|---|---|
| `SMA(n)` | Media aritmética de los últimos `n` cierres, incluyendo el actual |
| `Bollinger(n, k)` | `middle = SMA(n)`; `upper/lower = middle ± k × std(n)`, con desviación estándar **poblacional** (`ddof=0`) |
| `RSI(n)` | RSI de Wilder: medias de ganancias y pérdidas con suavizado de Wilder (`alpha = 1/n`) |
| `ATR(n)` | True Range = `max(high − low, |high − close_prev|, |low − close_prev|)`, suavizado de Wilder (`alpha = 1/n`) |
| `ADX(n)` | ADX de Wilder estándar (+DI, −DI, DX, suavizado de Wilder) |
| `Donchian high/low(n)` | Máximo de `high` / mínimo de `low` de las `n` velas **anteriores**, excluyendo la actual |

**IND-01.** Mientras un indicador no tenga suficientes velas para calcularse (período de calentamiento), su valor es `None` y ninguna condición que dependa de él puede ser verdadera.

### 3.5 Etiqueta de régimen de mercado

**REG-01.** Cada decisión y cada operación se etiquetan con el régimen en la última vela diaria completa:

- `tendencia`: `"alcista"` si cierre diario > SMA(200) diaria, si no `"bajista"`.
- `fuerza`: `"con_tendencia"` si ADX(14) diario > 25, si no `"lateral"`.

Etiqueta combinada, por ejemplo: `alcista_lateral`. Sirve solo para análisis; **no** es una condición de entrada.

### 3.6 Parámetros por defecto

| Parámetro | A | B |
|---|---|---|
| Período Bollinger / desviaciones | 20 / 2.0 | — |
| Período y umbral RSI | 14 / 30 | — |
| Velas máximas en posición | 48 | — |
| Ruptura (Donchian de entrada) | — | 20 |
| Salida (Donchian de salida) | — | 10 |
| Período y umbral ADX | — | 14 / 20 |
| ATR del stop / multiplicador | 14 / 2.0 | 14 / 2.0 |
| Filtro de régimen SMA diaria | 200 | 200 |

---

## 4. Gestión de riesgo

### 4.1 Límites (valores por defecto, configurables)

| ID | Límite | Valor | Efecto al alcanzarlo |
|---|---|---|---|
| RISK-01 | Riesgo por operación | 1% del capital | Define el tamaño (§4.2) |
| RISK-02 | Tamaño máximo de posición | 25% del capital | Tope al tamaño |
| RISK-03 | Posiciones simultáneas | 1 | Rechazo de nuevas entradas |
| RISK-04 | Pérdida diaria máxima | 3% | No se abren operaciones hasta el siguiente día UTC |
| RISK-05 | Alerta de drawdown | 10% | Alerta |
| RISK-06 | Drawdown máximo | 15% | Circuit breaker (apagado) |
| RISK-07 | Órdenes por hora | 6 | Circuit breaker (se asume bug) |

### 4.2 Dimensionamiento

```
riesgo_usd   = capital × risk_per_trade_pct / 100
distancia    = precio_entrada − stop_price
cantidad     = riesgo_usd / distancia
cantidad     = min(cantidad, capital × max_position_pct / 100 / precio_entrada)
cantidad     = redondear_hacia_abajo(cantidad, step_size del exchange)
```

**RISK-08.** Si la cantidad resultante tiene un nocional menor al mínimo del exchange, la señal se **rechaza** (nunca se redondea hacia arriba).

**RISK-09.** `stop_price` debe estar por debajo del precio de entrada, a una distancia entre 0,5% y 15%. Fuera de ese rango, la señal se rechaza como anómala.

### 4.3 Validación previa a cada orden

**RISK-10.** Toda orden pasa por `RiskManager.validate()` sin excepción ni bypass. Se verifica: símbolo permitido; lado permitido (solo compra para abrir); cantidad y nocional dentro de límites; filtros del exchange (`minNotional`, `stepSize`, `tickSize`) leídos desde la API, nunca escritos en el código; precio dentro de ±2% del último precio; saldo suficiente; señal no procesada antes (idempotencia por `signal_id`); límites RISK-01 a RISK-07; ningún circuit breaker abierto.

**RISK-11.** Toda decisión del RiskManager (aprobación o rechazo) se registra con su motivo en la bitácora (§7).

### 4.4 Circuit breakers

| ID | Condición |
|---|---|
| CB-01 | Drawdown ≥ 15% |
| CB-02 | 5 pérdidas consecutivas |
| CB-03 | Diferencia de reconciliación (posición o saldo interno ≠ exchange) |
| CB-04 | 3 errores de API consecutivos, o pérdida de conexión > 5 min con posición abierta |
| CB-05 | Slippage real > 3 × el asumido durante 5 operaciones consecutivas |
| CB-06 | Movimiento de precio > 8% en 1 hora (pausa) |
| CB-07 | Más de 6 órdenes en 1 hora |

**CB-08.** El estado de los breakers se persiste en SQLite y sobrevive reinicios. Un breaker abierto bloquea toda orden nueva de entrada. **Solo se cierra manualmente**, vía CLI con confirmación interactiva, y el cierre se registra con autor y motivo.

**CB-09.** Las salidas de protección (stop loss en el exchange) siguen activas aunque haya un breaker abierto.

### 4.5 Configuración y topes duros

**CFG-01.** Todos los límites viven en `config/*.yaml` y se validan con pydantic al arrancar.

**CFG-02. Topes duros en el código.** La configuración se rechaza (el bot no arranca) si algún valor sale de estos rangos:

| Clave | Rango permitido |
|---|---|
| `risk_per_trade_pct` | > 0 y ≤ 2 |
| `max_position_pct` | > 0 y ≤ 50 |
| `max_open_positions` | = 1 en v1 |
| `daily_loss_limit_pct` | > 0 y ≤ 5 |
| `drawdown_alert_pct` | > 0 y < `max_drawdown_pct` |
| `max_drawdown_pct` | > 0 y ≤ 25 |
| `max_orders_per_hour` | ≥ 1 y ≤ 12 |
| `max_consecutive_losses` | ≥ 2 y ≤ 10 |
| `max_capital_usd` (solo live) | > 0 y ≤ 1000 |

**CFG-03.** `config/live.yaml` solo lo modifica un humano. Su esquema de claves es el de `config/live.yaml` del repo.

**CFG-04.** Se calcula un `config_hash` (SHA-256 de la configuración efectiva normalizada, sin secretos) que se registra en cada fila de la bitácora.

### 4.6 Escalamiento de capital (live)

**ESC-01.** Nivel 1: 100 USD.

**ESC-02.** Para subir de nivel se requiere todo lo siguiente: ≥ 20 operaciones en vivo en el nivel actual; cero incidentes de seguridad o de reconciliación; slippage real < 2 × el asumido; drawdown dentro de límites.

**ESC-03.** Cada subida es como máximo el doble del nivel anterior. La decide y ejecuta un humano, editando `config/live.yaml`.

---

## 5. Ejecución

- **EXE-01.** Entradas y salidas por señal se ejecutan con **órdenes de mercado**.
- **EXE-02. Stop en el exchange:** inmediatamente después de confirmarse el llenado de una entrada, se coloca la orden de stop loss en Binance. Se usa `STOP_LOSS` (mercado) si el par lo admite según `exchangeInfo`; si no, `STOP_LOSS_LIMIT` con precio límite `stop_price × (1 − stop_limit_buffer_pct/100)`, con `stop_limit_buffer_pct = 0.5` por defecto.
- **EXE-03.** Si la orden de stop no puede colocarse tras los reintentos, la posición se **cierra a mercado** de inmediato y se abre el breaker CB-04.
- **EXE-04. Salida por señal:** (1) cancelar la orden de stop; (2) confirmar su estado; (3) si el stop ya se ejecutó, registrar la salida como `STOP` y no vender; (4) si fue cancelado, vender a mercado.
- **EXE-05. Máquina de estados de órdenes:** `CREATED → SUBMITTED → OPEN → (FILLED | PARTIALLY_FILLED | CANCELED | REJECTED | EXPIRED)`, con transiciones válidas explícitas. Cada transición se guarda en `order_events` (solo inserción).
- **EXE-06. Idempotencia:** `client_order_id` derivado del `signal_id`. Reenviar la misma señal no crea una segunda orden.
- **EXE-07. Reconciliación:** al arrancar y cada 10 minutos se compara posición, saldo y órdenes abiertas internas contra el exchange. Cualquier diferencia abre CB-03.
- **EXE-08. Tiempo:** todo en UTC. Se compensa el desfase con el reloj del servidor del exchange.
- **EXE-09. Modos:** `backtest`, `dry-run` (calcula todo, no envía órdenes), `paper` y `live`. El modo `live` exige, a la vez: flag `--mode live`, variable de entorno `CENTINELA_LIVE_CONFIRMED=yes` y confirmación interactiva al arrancar. **En el Sprint 1, `live` no se implementa** y debe rechazarse con un mensaje explícito.

---

## 6. Validación

- **VAL-01. Datos:** 4 años de velas BTC/USDT en 1h, 4h y 1d de Binance, con reporte de calidad (huecos, duplicados, nulos, `high < low`) antes de cualquier backtest.
- **VAL-02. Reserva final (holdout):** los últimos 6 meses del dataset quedan reservados. El cargador de datos **se niega** a entregar ese período salvo que se usen a la vez el flag `--use-holdout` y la variable `CENTINELA_ALLOW_HOLDOUT=yes`, y cada uso queda registrado. Se usa **una sola vez**, como examen final de la combinación elegida. Solo un humano lo activa.
- **VAL-03. Ventanas:** el período restante se evalúa completo y en ventanas móviles de 3 meses, reportando métricas por ventana y por régimen (REG-01).
- **VAL-04. Costos simulados:** comisión 0,1% por lado; slippage 0,05% por lado. Órdenes de mercado se llenan al **open de la vela siguiente** ± slippage.
- **VAL-05. Stop en backtest:** si el `low` de una vela toca el stop, se llena al `stop_price` menos slippage. Si la vela **abre** por debajo del stop (hueco), se llena al **open** menos slippage. Si en una misma vela se tocan stop y objetivo, se asume que ocurrió primero el **stop** (supuesto pesimista).
- **VAL-06. Paridad:** el backtest usa los **mismos** módulos de estrategia, riesgo y ejecución que paper y live; solo cambia el connector.
- **VAL-07. Métricas:** retorno total y anualizado, drawdown máximo y su duración, Sharpe, Sortino, tasa de acierto, profit factor, expectativa neta por operación, número de operaciones, exposición (% del tiempo en posición) y comparación con buy & hold del mismo período.
- **VAL-08. Sensibilidad:** cada parámetro se varía ±20% (uno a la vez); se reporta si cambia el signo de la expectativa neta.

### 6.5 Regla de comparación y elección

Se evalúan 4 combinaciones (A y B × 1h y 4h). **Una combinación califica** para paper trading solo si cumple todo, fuera de muestra:

- Expectativa neta por operación > 0.
- ≥ 60 operaciones.
- Profit factor > 1,3.
- Drawdown máximo < 15%.
- La sensibilidad (VAL-08) no invierte el signo en ningún parámetro.

Entre las que califiquen, se elige la de mayor expectativa neta. Si dos combinaciones difieren en menos de 20% de expectativa, se prefiere la de 4h. La elegida debe además aprobar el holdout (VAL-02). **Si ninguna califica, no se pasa a paper trading**: se itera (máximo 2 iteraciones, cada una registrada en un ADR) o se cambia de enfoque. La decisión se documenta en `docs/decisions/002-resultado-backtest.md`.

### 6.6 Gate de paper trading → live

Todo obligatorio:

- ≥ 8 semanas continuas y ≥ 20 operaciones.
- Disponibilidad ≥ 99% sin intervención manual no planificada.
- 0 violaciones de límites de riesgo; 0 órdenes inválidas enviadas.
- Diferencia < 20% entre resultado de paper y predicción del backtest para el mismo período.
- Expectativa neta > 0.
- Reconciliación automática funcionando.
- Kill switch probado con un simulacro documentado.

**GATE-01. Regla del reloj:** cualquier cambio de parámetros durante el paper trading reinicia el conteo de 8 semanas.

### 6.7 Prohibición de sobreajuste

**OVF-01.** Ningún agente cambia parámetros, umbrales, filtros o reglas de las estrategias con el fin de mejorar métricas de backtest. Las mejoras se proponen por escrito a un humano, con hipótesis previa, y solo se ejecutan en una tarea explícita de optimización con validación walk-forward.

**OVF-02.** El holdout no se usa para tomar decisiones intermedias. Mirar el holdout y después ajustar invalida el holdout.

---

## 7. Bitácora de decisiones (SQLite)

**LOG-01.** Todo se guarda en SQLite con el **mismo esquema** en backtest, paper y live. Las tablas son de **solo inserción**: no se hacen `UPDATE` destructivos ni `DELETE` (los cambios de estado se registran como filas nuevas).

**LOG-02.** Cada fila de `decisions` y `trades` incluye `run_id`, `strategy`, `strategy_version` y `config_hash`.

| Tabla | Una fila por | Campos mínimos |
|---|---|---|
| `runs` | Ejecución del bot o backtest | `run_id`, `mode`, `started_at`, `ended_at`, `git_commit`, `config_hash`, `strategy`, `strategy_version`, `timeframe` |
| `decisions` | **Cada vela evaluada, haya operación o no** | `id`, `run_id`, `candle_ts`, `timeframe`, `close`, `indicators` (JSON con todos los valores), `conditions` (JSON con cada condición y su resultado booleano), `regime`, `decision` (`ENTER`, `EXIT`, `HOLD`, `NONE`, `BLOCKED_RISK`, `BLOCKED_BREAKER`), `reason`, `signal_id` |
| `signals` | Señal emitida | `signal_id`, `decision_id`, `side`, `stop_price`, `reason`, `created_at` |
| `risk_decisions` | Validación del RiskManager | `signal_id`, `approved`, `reason`, `quantity`, `risk_usd`, `checks` (JSON) |
| `orders` | Orden | `order_id`, `client_order_id`, `signal_id`, `type`, `side`, `quantity`, `price`, `stop_price`, `created_at` |
| `order_events` | Transición de estado | `order_id`, `from_status`, `to_status`, `ts`, `raw` (respuesta cruda del exchange) |
| `trades` | Operación completa | `trade_id`, `entry_ts`, `entry_price`, `exit_ts`, `exit_price`, `quantity`, `exit_reason` (`TARGET`, `STOP`, `TIME`, `TREND_EXIT`, `BREAKER`, `MANUAL`), `fees_usd`, `slippage_entry_pct`, `slippage_exit_pct`, `pnl_usd`, `pnl_pct`, `mfe_pct`, `mae_pct`, `bars_held`, `regime_at_entry`, `entry_decision_id`, `exit_decision_id` |
| `breaker_events` | Apertura o cierre de breaker | `breaker`, `event` (`OPEN`/`CLOSE`), `ts`, `reason`, `actor` |
| `equity_snapshots` | Cierre de cada vela | `ts`, `equity_usd`, `cash_usd`, `position_value_usd`, `drawdown_pct` |

**LOG-03.** `mfe_pct` y `mae_pct`: máxima ganancia y máxima pérdida no realizadas, en %, alcanzadas mientras la operación estuvo abierta.

**LOG-04.** Además de SQLite, se emiten logs estructurados JSON (structlog) con `run_id` y la cadena `signal_id → order_id → trade_id`. Ningún log contiene valores de variables cuyo nombre incluya `key`, `secret` o `token`.

---

## 8. Arquitectura y contratos

- **ARQ-01.** Monolito modular en Python 3.14 (ver ADR-001).
- **ARQ-01b. Nombres:** repositorio `centinela-trade`, paquete de Python `centinela_trade` (en `src/centinela_trade/`), comando de terminal `centinela`. Donde `docs/plan.md` dice `tradebot` o `trading-ecosystem`, léase `centinela_trade` / `centinela-trade`.
- **ARQ-01c. Núcleo reutilizable:** `core/`, `risk/` (interfaces), `execution/`, `journal/` y `connectors/base.py` no deben depender de nada específico de spot ni de BTC. Lo específico del instrumento vive en `strategies/` y en las implementaciones de connectors. Esto permite que futuros bots de la familia Centinela (por ejemplo, opciones) reutilicen el núcleo.
- **ARQ-02. Dirección de dependencias:** Estrategia → `Signal` → RiskManager → orden aprobada → Execution → Connector. Nada río abajo llama río arriba; hacia arriba solo fluyen eventos y datos.
- **ARQ-03.** Los módulos se comunican **solo** mediante los tipos de `core/models.py`: `Candle`, `Signal`, `OrderRequest`, `ApprovedOrder`, `Rejection`, `Order`, `Fill`, `Position`, `Trade`, `PortfolioState`, `Decision`. Son inmutables (dataclasses `frozen` o modelos pydantic `frozen`). Los importes de dinero y cantidades usan `Decimal`.
- **ARQ-04. Interfaces abstractas** en `core/interfaces.py`: `Strategy`, `RiskManager`, `ExchangeConnector`, `Journal` (bitácora).
- **ARQ-05. Connectors:** `backtest` (datos históricos, fills según VAL-04/VAL-05), `paper` (precios en vivo, fills simulados pesimistas, estado persistido), `live_ccxt` (ccxt; en v1 solo apuntado a Demo Mode o Testnet).
- **ARQ-06.** Prohibido: imports circulares; que la estrategia importe un connector o el RiskManager; que el connector conozca la estrategia; que `notebooks/` sea importado por `src/`.

---

## 9. Monitoreo y reportes

- **MON-01. Reporte semanal** (corte lunes 00:00 UTC) generado desde la bitácora: métricas OBJ-03 y comparación OBJ-04.
- **MON-02.** Desde la Fase 3 (paper): alertas Telegram por cada operación, error, breaker y un heartbeat diario.
- **MON-03.** Kill switch por CLI: cancela órdenes abiertas, opcionalmente cierra la posición, abre un breaker manual y detiene el proceso.

---

## 10. Guardarraíles

Las reglas de comportamiento de los agentes están en `AGENTS.md` y son vinculantes. La política de riesgo y su justificación están en `docs/risk_policy.md`.

---

## 11. Definición de terminado del Sprint 1

El Sprint 1 termina cuando: (1) `centinela backtest` ejecuta las 4 combinaciones de §6.5 sobre el dataset sin holdout y produce un reporte reproducible con todas las métricas de VAL-07 y VAL-08; (2) `centinela run --mode dry-run` ejecuta el mismo loop con datos recientes sin enviar órdenes; (3) la bitácora contiene decisiones de todas las velas evaluadas; (4) `make lint` y `make test` pasan, con 100% de cobertura de ramas en `risk/` y `execution/`.

---

## Historial de cambios

| Versión | Fecha | Cambio | Autor |
|---|---|---|---|
| 1.0 | 2026-10-18 | Versión inicial aprobada | Juan Manuel Vásquez |
