# Plan de Implementación del Ecosistema Autónomo de Trading

> Documento técnico de planificación. Versión 1.0 — Julio 2026.
> Uso previsto: documento base para compartir con agentes IA (Codex, Claude Code, ChatGPT) y guiar el desarrollo.
> Nota obligatoria: nada en este documento es asesoría financiera ni promesa de rentabilidad. El trading algorítmico en cripto tiene alta probabilidad de pérdida de capital. Este plan optimiza para aprendizaje, control de riesgo y validación medible, no para ingresos.

---

## Índice

1. [Diagnóstico crítico del proyecto](#1-diagnóstico-crítico-del-proyecto)
2. [Separación entre bot inicial y ecosistema completo](#2-separación-entre-bot-inicial-y-ecosistema-completo)
3. [Propuesta de bot inicial MVP](#3-propuesta-de-bot-inicial-mvp)
4. [Estrategia de generación de ingresos inicial](#4-estrategia-de-generación-de-ingresos-inicial)
5. [Arquitectura modular del ecosistema](#5-arquitectura-modular-del-ecosistema)
6. [Roadmap por fases](#6-roadmap-por-fases)
7. [Organización del repositorio](#7-organización-del-repositorio)
8. [Stack tecnológico recomendado](#8-stack-tecnológico-recomendado)
9. [Protocolo para usar agentes IA](#9-protocolo-para-usar-agentes-ia)
10. [Seguridad y gestión de riesgo](#10-seguridad-y-gestión-de-riesgo)
11. [Diseño del primer sprint de desarrollo](#11-diseño-del-primer-sprint-de-desarrollo)
12. [Prompts iniciales para Codex/Claude Code](#12-prompts-iniciales-para-codexclaude-code)
13. [Métricas de éxito](#13-métricas-de-éxito)
14. [Crítica final](#14-crítica-final)
15. [Resumen ejecutivo accionable](#15-resumen-ejecutivo-accionable)
16. [Próximas acciones inmediatas](#próximas-acciones-inmediatas)

---

## 1. Diagnóstico crítico del proyecto

### 1.1 Qué partes tienen sentido

- **La descomposición modular.** Separar datos, estrategia, ejecución, riesgo y monitoreo es exactamente cómo se construyen sistemas de trading serios. Es la parte mejor pensada de tu visión.
- **Paper trading obligatorio antes de dinero real.** Correcto y no negociable.
- **Sin permisos de retiro, sin apalancamiento, límites estrictos.** Correcto.
- **El bot como generador de datos propios.** Esta es la idea más valiosa del proyecto: el activo real que construyes en los primeros 6 meses no es rentabilidad, es infraestructura + datos + registro de ejecución real (slippage, fees, latencia, fallos).
- **Rechazo explícito a promesas de ingresos pasivos.** Esa mentalidad es la única que puede sobrevivir en este dominio.

### 1.2 Qué partes son demasiado ambiciosas para el inicio

- **"Agentes IA para análisis, desarrollo y mejora continua" como módulo del sistema.** Agentes IA como *herramientas de desarrollo* (Claude Code escribiendo código que tú revisas): sí, desde el día uno. Agentes IA *dentro del loop de trading* (decidiendo, optimizando estrategias en producción): no antes de la Fase 7, y probablemente nunca sin supervisión humana. Un agente con capacidad de modificar estrategias en producción es un vector de pérdida catastrófica.
- **ML predictivo.** Sin al menos 6-12 meses de datos propios de ejecución y un pipeline de backtesting robusto, el ML solo producirá overfitting elegante. Las 2× RTX 3090 no te dan ventaja aquí todavía.
- **15 módulos desde el inicio.** El MVP necesita 6. El resto son interfaces vacías o carpetas futuras.
- **Market making y arbitraje.** Compites contra firmas con colocation, latencias de microsegundos y fees negativos. No es terreno para un MVP.

### 1.3 Riesgos que estás subestimando

| Riesgo | Por qué es grave |
|---|---|
| **Ausencia de edge** | El riesgo #1 no es técnico. Puedes construir un sistema impecable que ejecute perfectamente una estrategia sin ventaja estadística. La mayoría de estrategias simples en cripto spot pierden después de fees. |
| **Fees y slippage** | Con capital pequeño ($200-500), los fees de taker (~0.1%) por operación destruyen estrategias de alta frecuencia de señales. Una estrategia que "gana" 0.15% por trade en backtest pierde en real. |
| **Overfitting en backtesting** | Optimizar parámetros hasta que el backtest se vea bien garantiza fracaso en vivo. Es el error #1 de todo trader algorítmico novato. |
| **El hardware como distracción** | El rig con 2× RTX 3090 invita a hacer ML prematuro. Además, un Pentium G5420 con 8 GB de RAM es un cuello de botella severo para todo lo que no sea GPU. |
| **Confiabilidad operacional** | Un bot en vivo que se cae, pierde conexión, o queda en estado inconsistente con el exchange puede dejar posiciones abiertas sin gestión. La ingeniería de fallos es más difícil que la estrategia. |
| **Riesgo de contraparte** | El exchange puede congelar retiros, quebrar o cambiar su API. Capital en exchange = capital en riesgo aunque el bot no opere. |
| **Costo de oportunidad** | 6 meses de trabajo para (con suerte) mover $500 con retorno incierto. Si el objetivo real es ingreso, hay caminos más cortos (ver 14.6). |
| **Regulación/impuestos locales** | Las ganancias de trading tributan. Infórmate de tu obligación fiscal en Chile (SII trata cripto como renta) antes de operar en vivo. |

### 1.4 Decisiones que podrían destruir el proyecto

1. Ir a dinero real sin pasar criterios de salida de paper trading medibles.
2. Dar a agentes IA acceso a API keys o capacidad de desplegar a producción.
3. Optimizar parámetros sobre el mismo dataset que usas para validar (sin walk-forward / out-of-sample).
4. Construir los 15 módulos antes de tener un bot que complete el ciclo señal→orden→registro.
5. Usar apalancamiento o derivados "para acelerar resultados".
6. Aumentar capital tras una racha buena corta (< 3 meses de datos en vivo).
7. No tener kill switch manual y automático desde el primer día en vivo.

### 1.5 Qué simplificar

- Un solo exchange, un solo par (BTC/USDT), un solo timeframe (1h o 4h), una sola estrategia.
- Monolito modular (un solo proceso Python con módulos internos bien separados), no microservicios.
- SQLite + archivos Parquet, no cluster de bases de datos.
- Dashboard = logs estructurados + un notebook + alertas por Telegram. La UI web espera.

### 1.6 Qué evitar por ahora

- ML, agentes IA en el loop de trading, market making, arbitraje, derivados, multi-exchange, microservicios, Kubernetes, UI web compleja, más de 2 pares.

### 1.7 Obligatorio desde el día uno

- Control de versiones con revisión humana de cada cambio.
- Tests automatizados del risk manager y del ciclo de órdenes (cobertura ~100% en esos módulos).
- Logging estructurado y auditable de cada decisión y orden.
- Separación estricta de entornos (dev / paper / live) y de secretos.
- Modo dry-run como default: el bot nunca envía órdenes reales salvo configuración explícita y deliberada.
- Límites de riesgo codificados como capa independiente que la estrategia no puede saltarse.

---

## 2. Separación entre bot inicial y ecosistema completo

### 2.1 El bot inicial (Proyecto A — meses 0-4)

**Es:** un programa que ejecuta UNA estrategia simple, en UN par, en UN exchange, con riesgo acotado, primero en paper y luego con capital mínimo, registrando todo.

**Responsabilidades:**
- Descargar y almacenar OHLCV del par elegido.
- Calcular señales de la estrategia.
- Validar cada orden contra el risk manager.
- Ejecutar (simulado o real) y registrar cada evento.
- Detenerse solo ante cualquier condición anómala.

**Límites explícitos (lo que el bot NO es):**
- No es multi-estrategia, ni multi-exchange, ni multi-par.
- No aprende, no se auto-optimiza, no usa ML.
- No tiene UI. Se opera por CLI + archivos de configuración.
- No gestiona portafolio: gestiona UNA posición.

**Criterio de éxito del bot inicial:** no es "ganar dinero". Es: (a) operar 60+ días sin intervención no planificada, (b) que los trades reales coincidan ±tolerancia con lo que la simulación predecía, (c) generar un dataset de ejecución propio limpio.

### 2.2 El ecosistema completo (Proyecto B — meses 6+, condicional)

**Es:** una plataforma donde múltiples estrategias compiten por capital, con backtesting industrializado, ML lab, orquestación y dashboard. Solo tiene sentido construirlo si el Proyecto A demuestra que existe al menos una estrategia con edge medible después de fees, o si pivoteas el ecosistema hacia un producto para terceros (herramienta, no fondo).

**Regla de oro anti-"bot gigante desordenado":** el bot inicial se construye ya con las interfaces del ecosistema (`Strategy`, `RiskManager`, `ExchangeConnector`, `Broker` abstractos), pero con UNA implementación de cada una. El ecosistema crece agregando implementaciones, no reescribiendo. Si un cambio del ecosistema exige reescribir el bot, la arquitectura del bot estuvo mal.

| Dimensión | Bot inicial | Ecosistema |
|---|---|---|
| Estrategias | 1 | N, con asignación de capital |
| Pares | 1 (BTC/USDT) | Multi-activo |
| Exchange | 1 | Multi-exchange |
| Datos | OHLCV 1h/4h | Tick/orderbook + alternativos |
| ML | No | Lab con validación estricta |
| Agentes IA | Solo en desarrollo | Investigación asistida (nunca autonomía total en producción) |
| Infraestructura | 1 proceso + SQLite | Servicios + TSDB + colas |
| UI | CLI + Telegram | Dashboard web |

---

## 3. Propuesta de bot inicial MVP

### 3.1 Comparación de enfoques

| Enfoque | Complejidad | Riesgo | Fees/infra | Edge realista para retail | Valor de aprendizaje | Veredicto MVP |
|---|---|---|---|---|---|---|
| **Grid bot** | Baja | Medio-alto: acumula pérdidas en tendencias fuertes; "gana poco muchas veces, pierde mucho pocas veces" | Alto (muchas órdenes) | Bajo; edge negativo en tendencia | Medio | No |
| **DCA controlado** | Muy baja | Bajo si es solo acumulación | Bajo | No es trading: es inversión pasiva; no valida nada del ecosistema | Bajo | No (pero útil como benchmark) |
| **Mean reversion** | Baja-media | Medio, controlable con stops y filtro de régimen | Medio | Marginal pero medible; funciona en rangos, muere en tendencias | **Alto** | **Sí (elegido)** |
| **Trend following simple** | Baja | Medio; drawdowns largos, pocas señales | Bajo (pocas órdenes) | Marginal; históricamente uno de los pocos efectos persistentes | **Alto** | **Sí (candidato B / benchmark)** |
| **Market making** | Muy alta | Alto (inventario, selección adversa) | Requiere latencia baja y fees maker preferentes | Casi nulo para retail sin infraestructura | Alto pero caro | No |
| **Arbitraje** | Alta | Medio (riesgo de transferencia/ejecución) | Multi-exchange, capital fragmentado | Casi nulo; los spreads los cierran bots profesionales en ms | Medio | No |
| **Señales con indicadores** | Baja | Depende | Depende | Es la categoría que contiene mean reversion y trend following; no es una estrategia en sí | — | Marco, no estrategia |
| **ML predictivo** | Muy alta | Alto (overfitting invisible) | GPU, pipeline complejo | Negativo sin datos y proceso maduros | Alto pero prematuro | No (Fase 6) |

### 3.2 Elección: mean reversion simple con filtro de régimen, spot, sin apalancamiento

**Especificación v0 (parámetros iniciales razonables, NO optimizados — se validan en backtest):**

- Par: BTC/USDT spot. Timeframe: 1h (evaluar 4h en backtest).
- Señal de entrada (long only): precio cierra bajo la banda de Bollinger inferior (20, 2.0) **y** RSI(14) < 30.
- Filtro de régimen: solo operar si el precio está sobre la SMA(200) en el timeframe diario (evita comprar caídas dentro de mercados bajistas). Este filtro es lo que separa esta estrategia de "atrapar cuchillos".
- Salida: retorno a la media (banda media) **o** stop loss fijo (p.ej. -2.5%) **o** salida por tiempo (48 velas sin resolución).
- Tamaño de posición: fijo, definido por el risk manager (nunca por la estrategia). Máx. 1 posición abierta.
- Solo órdenes limit cuando sea posible (fee maker) con timeout y cancelación.

**Por qué esta y no otra:**
1. **Auditable:** cada trade tiene una razón explicable en una línea. Crítico para depurar y para aprender.
2. **Frecuencia moderada** (estimado 2-8 señales/mes): suficiente para generar datos, poca para que los fees dominen.
3. **Ejercita todo el ecosistema:** datos, señales, riesgo, ejecución, registro, reconciliación. Un DCA no ejercita casi nada; un market maker exige infraestructura que no tienes.
4. **Fracasa de forma informativa:** si pierde, sabrás exactamente en qué régimen y por qué. Con ML no sabrías.

**Benchmark obligatorio:** todo resultado se compara contra (a) buy & hold de BTC y (b) no hacer nada (USDT). Si el bot no supera ambos ajustado por riesgo, el bot no aporta.

**Advertencia honesta del quant:** la probabilidad de que esta estrategia con parámetros de libro tenga edge neto positivo sostenido es baja. Su función es ser el vehículo de validación del sistema. Si el backtest riguroso (Fase 2) muestra expectativa negativa después de fees, se ajusta o se cambia de estrategia — el sistema construido sirve igual para la siguiente.

---

## 4. Estrategia de generación de ingresos inicial

### 4.1 Qué significa "generar algo" de manera realista

Con $300-500 de capital y una estrategia marginal, "generar algo" significa **$0-15/mes en el mejor escenario, con meses negativos frecuentes**. En términos de ingreso, es ruido. El valor real de la fase inicial es:

1. Un sistema validado con dinero real (activo técnico).
2. Datos propios de ejecución (activo de datos).
3. Evidencia medible de si existe o no edge (activo de decisión).

**Si necesitas flujo de caja real este año, este proyecto no es el vehículo.** Trátalo como construcción de activo, y considera en paralelo monetizar las habilidades que el proyecto te hace desarrollar (ver 14.6).

### 4.2 Capital mínimo

- Paper trading: $0.
- Primer capital real: **$200-500**. Suficiente para superar los mínimos de orden del exchange (~$10-20 por orden en la mayoría) y para que fees/slippage sean medibles; poco suficiente como para que perderlo el 100% no te afecte. Regla: solo dinero cuya pérdida total aceptas hoy.
- No aumentar capital antes de 3 meses en vivo cumpliendo métricas (ver 4.5).

### 4.3 Expectativas que NO debes tener

- No habrá ingreso mensual confiable. No en 6 meses, probablemente no en 12.
- Un backtest bonito no predice resultados en vivo.
- Una buena racha de 2-4 semanas no es evidencia de edge (varianza).
- El hardware no genera ventaja. Las 3090 no imprimen alfa.
- Escalar capital no arregla una estrategia sin edge: amplifica la pérdida.

### 4.4 Métricas antes de poner dinero real (gate de salida de paper trading)

Todas deben cumplirse, medidas sobre **mínimo 8 semanas** de paper trading continuo:

- [ ] ≥ 20 trades ejecutados en paper (si hay menos, extender el periodo).
- [ ] Uptime del bot ≥ 99% sin intervención manual no planificada.
- [ ] 0 violaciones de límites de riesgo; 0 órdenes inválidas enviadas.
- [ ] Divergencia entre resultado de paper y lo que el backtest predecía para ese mismo periodo < 20% (valida que el simulador de fills es honesto).
- [ ] Expectativa por trade neta de fees > 0 en paper (no exige rentabilidad total, exige que el modelo no sea estructuralmente perdedor).
- [ ] Reconciliación diaria automatizada funcionando (estado interno == estado exchange).
- [ ] Kill switch manual y automático probados (simulacro documentado).

### 4.5 Transición y reglas en vivo

- **Drawdown máximo aceptable:** 15% del capital asignado → apagado automático + revisión completa antes de reiniciar. Alerta a 10%.
- **Límite de pérdida diaria:** 3% → el bot no abre más posiciones ese día.
- **Límite por operación:** riesgo máx. 1% del capital por trade (distancia al stop × tamaño).
- **Reglas de apagado automático (circuit breakers):**
  - Drawdown global ≥ 15%.
  - 5 pérdidas consecutivas.
  - Error de reconciliación (posición interna ≠ exchange).
  - 3 errores de API consecutivos o pérdida de conexión > 5 min con posición abierta → intentar cerrar posición y detenerse.
  - Slippage medido > 3× el asumido en backtest durante 5 trades.
  - Volatilidad extrema: movimiento > umbral (p.ej. 8% en 1h) → pausa.
- **Escalamiento:** solo tras 3 meses en vivo con métricas dentro de lo esperado, y en incrementos ≤ 2× por trimestre.

### 4.6 Mercados y condiciones

- **Primero:** BTC/USDT (máxima liquidez, spread mínimo, datos limpios). **Segundo (después):** ETH/USDT.
- Evitar: altcoins de baja capitalización (manipulación, spreads, riesgo de deslistado).
- **Condiciones que favorecen mean reversion:** mercado lateral/rango con volatilidad media, sin tendencia dominante.
- **Condiciones que la dañan:** tendencias fuertes sostenidas (el filtro SMA200 mitiga las bajistas; las alcistas causan lucro cesante, no pérdida), eventos de cola (crashes por liquidaciones en cascada — el stop loss puede ejecutarse con slippage severo), baja liquidez nocturna/fines de semana.
- Documentar el régimen de mercado de cada trade para poder analizar rendimiento por régimen después.

---

## 5. Arquitectura modular del ecosistema

### 5.1 Principios

1. **Monolito modular primero.** Un proceso Python, módulos con interfaces claras. Los microservicios llegan cuando haya un motivo operacional, no antes.
2. **Dependencias en una sola dirección:** Estrategia → (señales) → Risk Manager → (órdenes aprobadas) → Execution → Connector. Nada río abajo llama río arriba directamente; hacia arriba solo fluyen eventos/datos.
3. **La estrategia nunca toca dinero.** Emite intenciones (`SignalEvent`). Solo el Execution Engine, tras aprobación del Risk Manager, convierte intenciones en órdenes.
4. **Mismo código en backtest, paper y live.** Solo cambia la implementación del connector (histórico / simulado / real). Es la única forma de que el backtest signifique algo.

### 5.2 Módulos

| Módulo | Hace | NO hace | ¿MVP? |
|---|---|---|---|
| **Data Collector** | Descarga OHLCV vía API, valida gaps/duplicados, persiste | No transforma para estrategias, no calcula indicadores | ✅ |
| **Data Storage** | Parquet para históricos, SQLite para estado/órdenes/trades | No lógica de negocio | ✅ |
| **Strategy Engine** | Recibe velas, calcula indicadores, emite señales con razón y metadatos | No dimensiona posiciones, no envía órdenes, no conoce el capital | ✅ |
| **Risk Manager** | Valida cada señal contra límites; dimensiona posición; monitorea drawdown; dispara circuit breakers | No genera señales, no puede ser bypasseado, no tiene "excepciones" | ✅ |
| **Execution Engine** | Convierte órdenes aprobadas en llamadas al connector; maneja reintentos, timeouts, órdenes parciales; máquina de estados de cada orden | No decide qué operar ni cuánto | ✅ |
| **Exchange Connector** | Interfaz única (`place_order`, `cancel`, `get_balance`, `get_ohlcv`...) con 3 implementaciones: Backtest, Paper, Live (ccxt) | No lógica de estrategia ni riesgo | ✅ (backtest+paper primero) |
| **Paper Trading Engine** | Implementación simulada del connector contra datos en vivo: modela fees, slippage y fills parciales de forma pesimista | No usar fills optimistas (fill instantáneo al precio deseado = autoengaño) | ✅ |
| **Backtesting Engine** | Reproduce el loop del bot sobre histórico usando el connector de backtest; produce métricas y reporte | No optimización automática masiva de parámetros (eso es un módulo aparte con walk-forward) | ✅ |
| **Logging/Audit** | Log estructurado (JSON) de toda decisión, señal, orden y error, con IDs correlacionados | No se borra ni se rota destructivamente en live | ✅ |
| **Configuration Manager** | Config tipada y validada (pydantic) por entorno; secretos fuera del repo | No valores hardcodeados en código | ✅ |
| **Monitoring/Alerts** | Heartbeat, alertas Telegram (trade, error, circuit breaker, caída) | No dashboard web todavía | ✅ (mínimo) |
| **Portfolio Manager** | Asignación de capital entre estrategias, exposición agregada | — | ⏸ Fase 8 (en MVP es trivial: 1 estrategia) |
| **ML Lab** | Features, entrenamiento, validación walk-forward, registro de experimentos | Nunca despliega directo a producción | ⏸ Fase 6 |
| **Agent Orchestrator** | Coordina agentes IA para investigación/análisis con permisos acotados | Sin acceso a claves ni deploy | ⏸ Fase 7 |
| **Dashboard/API** | FastAPI read-only + UI | No acciones de trading desde la UI al inicio | ⏸ Fase 5 |

### 5.3 Comunicación y desacoplamiento

- **MVP:** llamadas directas entre módulos vía interfaces (clases abstractas / protocolos) + un event log persistente (tabla `events`). Sin colas de mensajes todavía.
- Todos los objetos de dominio (`Candle`, `Signal`, `Order`, `Trade`, `Position`) son dataclasses/pydantic inmutables compartidos en `core/models.py`. Los módulos se comunican solo con estos tipos, nunca con estructuras internas de otro módulo.
- Prohibido: imports circulares, que la estrategia importe el connector, que el connector conozca la estrategia.
- Cuando llegue el ecosistema: sustituir llamadas directas por bus de eventos (Redis Streams / NATS) sin cambiar los contratos.

```
[Data Collector] → [Storage] → [Strategy Engine] → SignalEvent
                                                      ↓
                                              [Risk Manager] → OrderRequest aprobada/rechazada
                                                      ↓
                                             [Execution Engine]
                                                      ↓
                                          [Exchange Connector (backtest|paper|live)]
                                                      ↓
                             fills/estado → [Storage] + [Logging] + [Alerts]
```

---

## 6. Roadmap por fases

> Duraciones asumen dedicación parcial (10-15 h/semana) con asistencia de agentes IA. Cada fase termina con una decisión explícita **seguir / detener / rehacer** documentada en `docs/decisions/`.

### Fase 0 — Preparación (1 semana)
- **Objetivo:** entorno, repo, decisiones base.
- **Entregables:** repo con estructura (§7), CI mínima (lint+tests), `AGENTS.md`/`CLAUDE.md`, cuenta de exchange creada (sin fondos, keys de solo lectura), documento de decisión de stack.
- **Éxito:** `make test` pasa en verde en un repo vacío pero estructurado.
- **Riesgo / no hacer:** perderse configurando el rig o hardware. **Desarrollar en tu máquina actual o un VPS de $5-10; el rig es Fase 6.**
- **Dependencias:** ninguna.

### Fase 1 — Bot MVP en local (2-3 semanas)
- **Objetivo:** ciclo completo datos→señal→riesgo→orden simulada→registro, corriendo contra datos históricos y en dry-run.
- **Entregables:** los 6 módulos MVP con tests; CLI (`bot run --mode dry-run`); connector simulado.
- **Éxito:** el bot procesa 2 años de histórico de BTC/USDT sin errores y registra cada decisión auditable.
- **No hacer:** conectar keys reales, optimizar parámetros, agregar pares.
- **Decisión:** si la arquitectura se siente frágil aquí, rehacer ahora (es barato).

### Fase 2 — Backtesting serio (2-3 semanas)
- **Objetivo:** saber si la estrategia merece paper trading.
- **Entregables:** backtester con fees/slippage pesimistas; validación walk-forward (train/test rodante); análisis por régimen; comparación vs buy&hold; reporte reproducible.
- **Éxito:** metodología correcta (no resultados bonitos): out-of-sample definido antes de optimizar, ≤ 3 parámetros ajustados, sensibilidad de parámetros analizada (si ±20% en un parámetro destruye el resultado, es overfitting).
- **Riesgo:** overfitting, lookahead bias (usar información del futuro), survivorship.
- **Decisión:** expectativa neta positiva estable out-of-sample → seguir. Negativa → iterar estrategia (máx. 2 iteraciones) o cambiar de enfoque. **No pasar a Fase 3 "para ver qué pasa".**

### Fase 3 — Paper trading (8+ semanas de reloj, poco esfuerzo activo)
- **Objetivo:** validar el sistema contra el mercado real sin dinero.
- **Entregables:** bot 24/7 en paper contra datos en vivo del exchange (testnet o simulación local con precios reales); alertas Telegram; reconciliación; reporte semanal automático.
- **Éxito:** gate completo de §4.4.
- **No hacer:** acortar el periodo porque "va bien"; tocar parámetros a mitad de periodo (si los cambias, el reloj se reinicia).
- **Decisión:** gate cumplido → Fase 4. Sistema inestable → arreglar y repetir. Estrategia claramente perdedora → volver a Fase 2.

### Fase 4 — Live con capital mínimo (12 semanas)
- **Objetivo:** medir la realidad: slippage, fills, fees, comportamiento psicológico propio.
- **Entregables:** keys de trading sin retiro; $200-500; todos los circuit breakers activos y probados; runbook de incidentes.
- **Éxito:** 3 meses operando dentro de parámetros; divergencia live vs paper explicable; cero incidentes de seguridad.
- **No hacer:** aumentar capital, agregar estrategias, "ajustar" tras una mala semana.
- **Decisión:** métricas OK → Fase 5. Edge inexistente pero sistema sólido → el sistema es el activo; iterar estrategia. Incidentes de seguridad/estado → detener y auditar.

### Fase 5 — Monitoreo y mejora (continuo, 4-6 semanas de trabajo)
- Dashboard read-only (FastAPI + frontend simple), métricas automatizadas, análisis post-trade, mejora del pipeline de datos. Segunda estrategia solo si la primera está estable.

### Fase 6 — ML experimental (8+ semanas, condicional)
- **Prerequisito:** ≥ 6 meses de datos propios + backtesting maduro. Aquí sí: montar el rig (upgrade a 32-64 GB RAM, NVMe, Ubuntu Server + Docker; el Pentium limitará el preprocesamiento — considerar upgrade de CPU o preprocesar en otra máquina).
- Objetivo: features sobre datos propios, modelos simples (gradient boosting antes que deep learning), validación walk-forward estricta. El ML propone; las reglas de riesgo disponen.
- **No hacer:** desplegar un modelo a live sin el mismo gate de paper trading que cualquier estrategia.

### Fase 7 — Agentes IA avanzados (condicional)
- Agentes para: análisis post-trade, generación de reportes, propuesta de hipótesis de estrategia, mantenimiento de código con revisión humana. **Nunca:** modificar producción sin revisión, acceso a claves, aumento autónomo de riesgo.

### Fase 8 — Escalamiento (condicional a edge demostrado o pivote a producto)
- Multi-estrategia con portfolio manager, multi-exchange, bus de eventos, TSDB (TimescaleDB/QuestDB), alta disponibilidad. Alternativa legítima: pivotear el ecosistema a producto/herramienta para otros (mejor razón riesgo/retorno que gestionar capital propio pequeño).

---

## 7. Organización del repositorio

```
trading-ecosystem/
├── README.md
├── CLAUDE.md                  # Reglas para agentes IA (ver §9)
├── AGENTS.md -> CLAUDE.md     # Mismo contenido para otros agentes
├── Makefile                   # make setup / test / lint / backtest / run-dry
├── pyproject.toml             # deps, ruff, mypy, pytest config
├── .env.example               # variables SIN valores reales
├── .gitignore                 # incluye .env, data/, logs/, secrets
├── docker-compose.yml
├── config/
│   ├── base.yaml              # config común
│   ├── backtest.yaml
│   ├── paper.yaml
│   └── live.yaml              # límites de riesgo MÁS estrictos aquí
├── src/tradebot/
│   ├── core/                  # models.py (Candle, Signal, Order, Trade),
│   │   │                      # events.py, exceptions.py, interfaces.py
│   ├── config/                # carga y validación pydantic
│   ├── data/                  # collector.py, storage.py, validation.py
│   ├── strategies/            # base.py (ABC), mean_reversion.py
│   ├── risk/                  # manager.py, limits.py, circuit_breakers.py
│   ├── execution/             # engine.py, order_state.py
│   ├── connectors/            # base.py (ABC), backtest.py, paper.py, live_ccxt.py
│   ├── backtesting/           # engine.py, metrics.py, report.py, walkforward.py
│   ├── monitoring/            # alerts.py (telegram), heartbeat.py
│   ├── logging/               # setup.py (structlog JSON)
│   └── cli.py                 # entrypoint: run, backtest, collect, report
├── tests/
│   ├── unit/                  # espejo de src/; risk/ y execution/ al 100%
│   ├── integration/           # ciclo completo en dry-run
│   └── fixtures/              # velas sintéticas, escenarios de mercado
├── scripts/                   # download_history.py, weekly_report.py
├── notebooks/                 # análisis exploratorio (NUNCA lógica de producción)
├── data/                      # (gitignored) raw/ processed/ (parquet)
├── logs/                      # (gitignored)
├── infra/                     # Dockerfile, systemd units, provisioning futuro
├── dashboard/                 # vacío hasta Fase 5
└── docs/
    ├── architecture.md
    ├── decisions/             # ADRs: 001-stack.md, 002-estrategia.md...
    ├── runbook.md             # qué hacer si algo falla
    └── risk_policy.md         # límites y su justificación (fuente de verdad)
```

Reglas: `notebooks/` jamás importado por `src/`; ningún secreto en el repo (pre-commit con detect-secrets); todo cambio a `src/tradebot/risk/` exige revisión humana línea por línea.

---

## 8. Stack tecnológico recomendado

| Área | Elección | Justificación |
|---|---|---|
| Lenguaje | **Python 3.12+** | Ecosistema quant/ML, agentes IA lo escriben bien; la latencia no importa a 1h/4h |
| Trading/exchange | **ccxt** | Estándar de facto, abstrae exchanges, facilita multi-exchange futuro |
| Datos | **pandas** (+ **polars** si el volumen crece), pyarrow/Parquet | Suficiente para OHLCV; Parquet es portable y barato |
| Base de datos | **SQLite** (estado, órdenes, trades) + Parquet (históricos) → **PostgreSQL/TimescaleDB** en Fase 8 | No montes Postgres para 1 bot y 1 par |
| Backtesting | **Motor propio simple** (mismo loop del bot) + **vectorbt** para exploración rápida en notebooks | El motor propio garantiza paridad backtest/live, que es lo que importa |
| Validación config | **pydantic v2** + YAML | Config tipada, errores tempranos |
| API | **FastAPI** (Fase 5, read-only primero) | — |
| Dashboard | Fase 5: **Streamlit** (rápido) → React si se vuelve producto | — |
| Scheduler | **APScheduler** dentro del proceso; **systemd** para mantener vivo el bot | Cron/K8s innecesarios aún |
| Logs | **structlog** (JSON) + rotación; **Loki+Grafana** solo en Fase 8 | — |
| Testing | **pytest** + pytest-cov + **hypothesis** (property testing del risk manager) + **freezegun** | — |
| Lint/tipos | **ruff** + **mypy** (estricto en core/, risk/, execution/) | Los tipos frenan errores de agentes IA |
| Contenedores | **Docker + docker-compose** | Paridad dev/prod |
| ML (Fase 6) | scikit-learn, XGBoost/LightGBM primero; PyTorch después | Modelos simples primero, siempre |
| Experiment tracking | **MLflow** (Fase 6) local en el rig | — |
| Deploy MVP | **VPS pequeño ($5-10/mes: Hetzner/DigitalOcean)** con Docker + systemd | Un bot live necesita uptime y red estables; un rig doméstico con Pentium y cortes de luz, no. El rig queda para entrenamiento ML (Fase 6) |
| Deploy futuro | Docker Compose en VPS mayor; K8s solo si hay razón real | — |
| Secretos | `.env` local + variables de entorno en VPS; **nunca en el repo**; considerar `sops`/age para respaldos cifrados | — |

**Sobre el rig:** para el MVP es innecesario y contraproducente (consumo eléctrico de 2× 3090 ociosas, punto único de fallo doméstico). Cuando llegue Fase 6: 64 GB RAM, NVMe 2 TB, Ubuntu Server 24.04, drivers NVIDIA + Docker con nvidia-container-toolkit, acceso remoto solo por SSH con llaves + Tailscale/WireGuard (no abrir puertos al internet).

---

## 9. Protocolo para usar agentes IA

### 9.1 Roles

| Agente | Puede | No debe |
|---|---|---|
| **ChatGPT / Claude (chat)** | Arquitectura, revisión de diseño, redacción de ADRs, análisis de resultados, redacción de prompts para agentes de código | Escribir código de producción directo a repo; decidir parámetros de riesgo |
| **Claude Code / Codex (agentes de código)** | Implementar tareas acotadas, escribir tests, refactorizar con tests en verde, documentar | Tocar `risk/` sin instrucción explícita; modificar config `live.yaml`; instalar dependencias no aprobadas; hacer push a `main`; acceder a `.env` |
| **Ningún agente** | — | Ver o manejar API keys reales; ejecutar el bot en modo live; desplegar a producción; "optimizar" límites de riesgo |

### 9.2 Protocolo de operación para agentes IA (copiar a `CLAUDE.md`)

```markdown
# Reglas para agentes IA en este repositorio

## Contexto
Bot de trading. Errores aquí pueden costar dinero real. La prudencia gana a la velocidad.

## Prohibido absolutamente
1. Leer, escribir o loggear secretos (.env, API keys). Si encuentras un secreto expuesto, detente y repórtalo.
2. Modificar src/tradebot/risk/, config/live.yaml o docs/risk_policy.md salvo instrucción explícita que lo mencione.
3. Enviar órdenes reales o ejecutar el bot en modo distinto a dry-run/backtest.
4. Eliminar o debilitar tests, validaciones o límites para "hacer pasar" algo.
5. Agregar dependencias sin listarlas y justificarlas en el resumen del cambio.
6. Hacer push directo a main. Todo va por rama + PR.

## Obligatorio
1. Toda función nueva llega con tests. risk/ y execution/: cobertura 100% de ramas.
2. `make lint` y `make test` en verde antes de declarar terminada una tarea.
3. Tipado estricto en core/, risk/, execution/ (mypy sin errores).
4. Un cambio = una tarea. No hacer refactors oportunistas fuera del alcance pedido.
5. Commits atómicos con formato: tipo(módulo): descripción (feat/fix/test/docs/refactor).
6. Actualizar docstrings y docs/ cuando cambies interfaces.
7. Si una instrucción contradice estas reglas o la arquitectura (docs/architecture.md), detente y pregunta.

## Arquitectura (resumen vinculante)
- La estrategia emite Signal; nunca crea órdenes ni conoce el capital.
- Toda orden pasa por RiskManager.validate() sin excepción ni bypass.
- Los módulos solo se comunican mediante los tipos de core/models.py.
- Mismo loop de bot en backtest, paper y live; solo cambia el connector.
```

### 9.3 Cómo entregar tareas

- **Una tarea = un módulo o una función, con criterios de aceptación y tests esperados.** Nunca "hazme el bot".
- Estructura de prompt: contexto (2 líneas) → tarea → interfaz exacta a implementar → restricciones → criterios de aceptación → tests requeridos.
- **Revisión de cambios:** leer el diff completo tú mismo (no pedirle al mismo agente que se autoapruebe). Para `risk/`, `execution/` y `connectors/`: revisión línea por línea + pedir a un *segundo* agente una revisión adversarial ("encuentra cómo este código podría perder dinero").
- **Commits:** el agente trabaja en rama; tú haces merge. Nunca des a un agente permisos de merge o deploy.
- **Permisos en la máquina:** agentes corren en el entorno de desarrollo con un usuario sin acceso a `.env` de paper/live; el VPS de producción no tiene agentes instalados; deploy manual vía script que tú ejecutas.
- **Documentación y tests:** exigirlos en el prompt, no después ("la tarea no está completa sin tests que cubran X, Y, Z y docstring de la interfaz").

---

## 10. Seguridad y gestión de riesgo

### 10.1 API keys y accesos

- [ ] Keys con permisos **solo trade + lectura. Retiro deshabilitado. Siempre.** Verificarlo en el exchange, no asumirlo.
- [ ] Restricción por IP (whitelist del VPS) cuando el exchange lo permita.
- [ ] Keys distintas por entorno (dev: solo lectura; paper: testnet o solo lectura; live: trade sin retiro).
- [ ] Secretos solo en variables de entorno / `.env` fuera de git; pre-commit `detect-secrets`.
- [ ] Rotación de keys cada 90 días y ante cualquier sospecha.
- [ ] 2FA en el exchange con app (no SMS); email dedicado con 2FA.

### 10.2 Límites (codificados en `risk/`, valores en `docs/risk_policy.md`)

| Límite | Valor inicial |
|---|---|
| Capital total asignado al bot | $200-500 |
| Riesgo por operación | ≤ 1% del capital |
| Tamaño máximo de posición | ≤ 25% del capital |
| Posiciones simultáneas | 1 |
| Pérdida diaria máxima | 3% → no abrir más ese día |
| Drawdown máximo global | 10% alerta, 15% apagado |
| Órdenes por hora (anti-loop) | ≤ 6; excederlo = bug = apagado |

### 10.3 Controles operacionales

- **Validación pre-orden:** símbolo permitido, lado esperado, tamaño dentro de límites, precio dentro de banda vs último precio (±2%), balance suficiente, sin orden duplicada (idempotency key por señal).
- **Registro:** toda orden con estado (created→submitted→open→filled/canceled/rejected), timestamps, respuesta cruda del exchange, y el `signal_id` que la originó. Append-only.
- **Reconciliación:** cada 5-15 min comparar posición/balance interno vs exchange. Divergencia → circuit breaker.
- **Dry-run por defecto:** `mode: live` exige flag explícito + variable de entorno + confirmación interactiva al arrancar.
- **Circuit breakers** (§4.5) implementados como capa que corta la ejecución, no como "if" dentro de la estrategia.
- **Alertas Telegram:** cada trade, cada error, cada breaker, heartbeat diario ("sigo vivo, estado X").
- **Backups:** SQLite y logs respaldados diariamente (cifrados) fuera del VPS.
- **Separación de entornos:** repos de config separados por entorno; la máquina de desarrollo jamás tiene keys live.
- **Si el bot se comporta raro:** (1) kill switch (comando que cancela órdenes abiertas, opcionalmente cierra posición y detiene el proceso), (2) verificar estado en el exchange manualmente, (3) congelar: no redeployar "un fix rápido", (4) post-mortem escrito en `docs/decisions/`, (5) reiniciar solo tras reproducir el fallo en test.

---

## 11. Diseño del primer sprint de desarrollo

### Sprint 0 — Fundaciones (3-5 días)

**Objetivo:** repo profesional, vacío de lógica pero con estructura, tooling y reglas listas para que los agentes trabajen sin romper nada.

**Tareas en orden:**
1. Crear repo con estructura de §7 (prompt P1).
2. `pyproject.toml` con ruff, mypy, pytest; `Makefile`; pre-commit con detect-secrets.
3. `CLAUDE.md` con el protocolo de §9.2.
4. `core/models.py` (Candle, Signal, Order, Trade, Position) + `core/interfaces.py` (Strategy, Connector, RiskManager abstractos) — **esto lo diseñas/revisas tú con máximo cuidado: son los contratos de todo el sistema.**
5. Config pydantic + YAMLs por entorno (prompt P2).
6. CI local: `make lint && make test` en verde.
7. `docs/architecture.md` y `docs/risk_policy.md` v0.

**Criterios de aceptación:** repo clona-instala-testea en < 5 min; mypy estricto en core/; ningún secreto; ADR-001 (stack) escrito.

**Decisiones técnicas cerradas en este sprint:** Python 3.12, ccxt, SQLite+Parquet, structlog, monolito modular, BTC/USDT 1h.

### Sprint 1 — Ciclo completo en dry-run (7-10 días)

**Objetivo:** `tradebot backtest` corre la estrategia sobre 2 años de histórico y produce un reporte; `tradebot run --mode dry-run` corre el mismo loop contra datos recientes sin enviar nada.

**Orden de implementación (cada paso = un prompt, un PR, una revisión):**
1. Data Collector + Storage: descarga OHLCV de Binance vía ccxt a Parquet, con validación de gaps (P3).
2. Strategy base + MeanReversion (P4).
3. Risk Manager básico con límites de §10.2 (P5) — revisión humana línea por línea.
4. Connector de backtest (fills pesimistas: fee taker 0.1%, slippage 0.05%) (P6).
5. Execution Engine con máquina de estados de órdenes (P7).
6. Backtesting Engine + métricas + reporte (P8).
7. Logging estructurado transversal (P9).
8. CLI + integración + test end-to-end (P10).

**Tests mínimos:** unit por módulo; property tests del risk manager (hypothesis: "ninguna combinación de inputs produce una orden que exceda límites"); integración end-to-end con velas sintéticas (escenario alcista, bajista, lateral, crash).

**Resultado del sprint:** un backtest reproducible con métricas honestas y un bot que corre en dry-run. Con esto tomas la primera decisión seguir/iterar de Fase 2.

---

## 12. Prompts iniciales para Codex/Claude Code

> Usar uno por vez, en rama nueva, revisando el diff antes del siguiente. Todos asumen que `CLAUDE.md` existe en el repo.

### P1 — Estructura inicial del repo

```
Crea la estructura inicial de un repositorio Python llamado trading-ecosystem.

TAREA
- Estructura de carpetas exacta: [pegar árbol de la sección 7 del plan]
- pyproject.toml: Python 3.12, deps: ccxt, pandas, pyarrow, pydantic>=2, structlog, typer, pytest, pytest-cov, hypothesis, ruff, mypy, freezegun, pre-commit.
- Makefile con targets: setup, lint (ruff+mypy), test (pytest con cobertura), format.
- .gitignore (incluye .env, data/, logs/, __pycache__), .env.example con claves BINANCE_API_KEY/SECRET y TELEGRAM_BOT_TOKEN/CHAT_ID vacías.
- pre-commit con ruff y detect-secrets.
- README.md breve: qué es, cómo instalar, comandos make.
- Paquetes vacíos con __init__.py y docstring de propósito de cada módulo.

RESTRICCIONES
- Sin lógica de negocio todavía. Sin dependencias extra.

CRITERIOS DE ACEPTACIÓN
- pip install -e ".[dev]" funciona; make lint y make test pasan (con al menos 1 test placeholder).
```

### P2 — Configuración base

```
Implementa el sistema de configuración en src/tradebot/config/.

TAREA
- Modelos pydantic v2: AppConfig { environment, exchange: ExchangeConfig, strategy: StrategyConfig, risk: RiskConfig, logging: LoggingConfig }.
- RiskConfig: max_capital_usd, risk_per_trade_pct, max_position_pct, max_open_positions, daily_loss_limit_pct, max_drawdown_pct, max_orders_per_hour. Todos con ge/le acotados (p.ej. risk_per_trade_pct entre 0 y 2).
- Carga: config/base.yaml + override por entorno (backtest|paper|live) + variables de entorno para secretos. Función load_config(env: str) -> AppConfig.
- Los secretos NUNCA se leen desde YAML, solo desde entorno.
- config/live.yaml debe fallar validación si max_capital_usd > 1000 (guardrail inicial).

CRITERIOS DE ACEPTACIÓN
- Tests: carga válida por entorno, error claro ante campo faltante o fuera de rango, secreto ausente produce error explícito, override funciona.
- mypy estricto sin errores.
```

### P3 — Data Collector + Storage

```
Implementa src/tradebot/data/ (collector.py, storage.py, validation.py).

TAREA
- Collector: descarga OHLCV de Binance spot vía ccxt (par y timeframe por parámetro), paginando históricos, con reintentos exponenciales y respeto de rate limits.
- Storage: persistencia en Parquet particionado por par/timeframe/año en data/raw/; función de lectura que devuelve DataFrame ordenado y sin duplicados.
- Validation: detectar gaps de velas, duplicados, valores nulos, velas con high<low. Reporte de calidad como dict.
- Script scripts/download_history.py: descarga N años de BTC/USDT 1h y 1d e imprime el reporte de calidad.

RESTRICCIONES
- Sin API keys (endpoints públicos). Sin indicadores ni lógica de estrategia aquí.

CRITERIOS DE ACEPTACIÓN
- Tests con respuestas ccxt mockeadas: paginación, gaps detectados, idempotencia (re-descargar no duplica).
```

### P4 — Motor de estrategia

```
Implementa src/tradebot/strategies/.

TAREA
- base.py: clase abstracta Strategy con on_candle(candle, history) -> Signal | None y propiedades name, params. La estrategia NO conoce capital, posiciones ni órdenes; solo datos de mercado y su propio estado de señal.
- mean_reversion.py: MeanReversionStrategy según spec:
  * Entrada long: cierre < banda Bollinger inferior(20, 2.0) Y RSI(14) < 30 Y precio diario > SMA(200) diaria (el filtro de régimen recibe la serie diaria por parámetro).
  * Salida: cierre >= banda media, o stop -2.5% desde entrada, o 48 velas sin salida.
  * Emite Signal con: side, reason (string legible), indicadores usados, timestamp, id único.
- Indicadores implementados con pandas puro (sin TA-Lib), en un módulo indicators.py testeado contra valores conocidos.

RESTRICCIONES
- Prohibido lookahead: solo velas cerradas hasta t. Sin acceso a connector, riesgo o config global.

CRITERIOS DE ACEPTACIÓN
- Tests con fixtures sintéticas: genera señal en escenario de sobreventa en rango; NO genera señal bajo SMA200; stop y salida por tiempo correctos; test explícito anti-lookahead (la señal en t no cambia si modifico velas posteriores a t).
```

### P5 — Risk Manager

```
Implementa src/tradebot/risk/ (manager.py, circuit_breakers.py). Este es el módulo más crítico del sistema: prioriza claridad y exhaustividad sobre elegancia.

TAREA
- RiskManager.validate(signal, portfolio_state) -> ApprovedOrder | Rejection(reason).
- Dimensionamiento: tamaño = (capital * risk_per_trade_pct) / distancia_al_stop, tope max_position_pct.
- Chequeos: límites de §10.2 del plan (capital, posición, posiciones abiertas, pérdida diaria, drawdown, órdenes/hora), precio dentro de ±2% del último precio, balance suficiente, no duplicar señal ya procesada.
- CircuitBreakers: drawdown >= 15%, 5 pérdidas consecutivas, error de reconciliación, errores de API consecutivos, slippage anómalo. Estado del breaker persistido en SQLite (sobrevive reinicios). Una vez abierto, solo se cierra manualmente vía CLI con confirmación.
- Toda decisión (aprobación o rechazo) se registra con razón.

RESTRICCIONES
- Sin dependencias de estrategia ni connector. Funciones puras donde sea posible.

CRITERIOS DE ACEPTACIÓN
- Cobertura 100% de ramas. Property tests (hypothesis): para cualquier input, la orden aprobada nunca excede ningún límite; con breaker abierto, nada se aprueba.
```

### P6 — Connector simulado (backtest/paper)

```
Implementa src/tradebot/connectors/ (base.py, backtest.py, paper.py).

TAREA
- base.py: ABC ExchangeConnector: get_ohlcv, get_balance, get_position, place_order, cancel_order, get_order_status, get_last_price.
- backtest.py: opera sobre DataFrames históricos; fills pesimistas: órdenes market se llenan al open de la vela siguiente + slippage 0.05%; fee 0.1% por lado; las limit solo se llenan si el precio las cruza. Mantiene balance y posición simulados.
- paper.py: igual lógica de fills pero con precios en vivo vía ccxt (endpoints públicos, sin keys). Persiste estado en SQLite para sobrevivir reinicios.

RESTRICCIONES
- Prohibido fill optimista (llenar al precio de la señal). Sin código de exchange real (live_ccxt.py queda para otra tarea).

CRITERIOS DE ACEPTACIÓN
- Tests: fills, fees y slippage con valores exactos esperados; limit no cruzada no se llena; balance nunca negativo; estado de paper sobrevive un reinicio simulado.
```

### P7 — Execution Engine

```
Implementa src/tradebot/execution/engine.py y order_state.py.

TAREA
- Recibe ApprovedOrder del RiskManager y la ejecuta vía connector.
- Máquina de estados por orden: CREATED→SUBMITTED→OPEN→(FILLED|PARTIALLY_FILLED|CANCELED|REJECTED|EXPIRED), con transiciones válidas explícitas y persistencia en SQLite (tabla orders, append-only para historial de transiciones).
- Idempotencia: client_order_id derivado del signal_id; reenviar la misma señal no crea segunda orden.
- Timeouts de órdenes limit con cancelación; reintentos con backoff ante errores transitorios; ante error persistente, reporta al circuit breaker.

CRITERIOS DE ACEPTACIÓN
- Tests: transiciones inválidas lanzan excepción; idempotencia; timeout cancela; fallo de connector no deja estado inconsistente (verificado con connector mock que falla a mitad).
```

### P8 — Backtesting Engine

```
Implementa src/tradebot/backtesting/ (engine.py, metrics.py, report.py).

TAREA
- engine.py: reproduce el loop real del bot (strategy→risk→execution→connector backtest) vela a vela sobre histórico. Debe usar LOS MISMOS módulos de producción, no una reimplementación vectorizada.
- metrics.py: retorno total y anualizado, max drawdown y duración, Sharpe y Sortino (retornos por periodo), win rate, profit factor, expectativa por trade neta de fees, número de trades, exposición, comparación vs buy&hold del mismo periodo.
- report.py: reporte markdown + curva de equity y drawdown (matplotlib) guardados en data/reports/<timestamp>/, incluyendo config y hash de git para reproducibilidad.
- walkforward.py: partición rodante train/test (p.ej. 12 meses train / 3 test) que ejecuta el backtest por ventanas y agrega resultados out-of-sample.

CRITERIOS DE ACEPTACIÓN
- Test de paridad: 100 velas procesadas por el backtester == mismas decisiones que el bot en dry-run con esas velas. Test con estrategia trivial de resultado conocido a mano.
```

### P9 — Logging estructurado

```
Implementa src/tradebot/logging/setup.py e intégralo en todos los módulos existentes.

TAREA
- structlog en JSON a archivo (logs/<env>/) y legible en consola; run_id por ejecución; correlación signal_id→order_id→trade_id en todos los eventos; niveles por módulo configurables.
- Eventos mínimos: candle_processed (debug), signal_generated, order_validated/rejected, order_submitted/filled/canceled, breaker_opened, reconciliation_result, error.
- Filtro que impide loggear cualquier valor de variables cuyo nombre contenga key/secret/token.

CRITERIOS DE ACEPTACIÓN
- Test: un ciclo completo produce la cadena de eventos correlacionados; test de que un secreto pasado por error queda redactado.
```

### P10 — Bot MVP integrado (dry-run) + CLI

```
Implementa src/tradebot/cli.py (typer) y el orquestador del bot.

TAREA
- Comandos: tradebot collect (descarga datos), tradebot backtest --config config/backtest.yaml, tradebot run --mode dry-run|paper (live NO implementado aún: debe rechazar con mensaje), tradebot report.
- Bot loop: cada nueva vela cerrada → strategy → risk → execution (connector según modo) → logs. Scheduler con APScheduler. Apagado limpio con SIGTERM (cancela órdenes abiertas en paper).
- Modo dry-run: connector de paper pero con envío de órdenes deshabilitado; solo registra lo que HABRÍA hecho.

CRITERIOS DE ACEPTACIÓN
- Test de integración end-to-end: con fixtures sintéticas, el bot completa ciclos y los logs muestran la cadena completa. tradebot run --mode live falla explícitamente.
- README actualizado con el flujo completo de uso.
```

---

## 13. Métricas de éxito

### Desarrollo y calidad técnica
- Cobertura de tests: global ≥ 80%; `risk/` y `execution/` = 100% de ramas.
- mypy sin errores en core/risk/execution; ruff limpio.
- PRs revisados por humano: 100%. Tamaño medio de PR < 400 líneas.
- Bugs que llegan a paper/live por sprint (objetivo: tendencia a 0).

### Backtesting (medir SIEMPRE out-of-sample)
- Expectativa por trade neta de fees (la métrica reina).
- Profit factor > 1.3 out-of-sample para considerar seguir.
- Max drawdown y su duración; Sharpe > 1 y Sortino como referencia (con cautela: pocas muestras).
- Sensibilidad de parámetros (variación ±20% no debe invertir el signo del resultado).
- Nº de trades ≥ 60-100 para significancia mínima.

### Paper trading
- Uptime ≥ 99%; errores de ejecución = 0 críticos.
- Divergencia paper vs backtest (mismo periodo) < 20%.
- Latencia señal→orden < 5 s; reconciliaciones exitosas 100%.

### Live
- Slippage real vs modelado (si real > 2× modelado, el backtest miente).
- Fees reales acumulados vs estimados.
- Divergencia live vs paper; fills parciales y rechazos del exchange.
- Todas las de paper, más P&L neto, drawdown en vivo, win rate, profit factor.

### Riesgo y operación
- Violaciones de límites: 0 (una sola es incidente con post-mortem).
- Activaciones de circuit breaker (cada una, documentada).
- Tiempo de detección de anomalías (alerta → tú enterado) < 5 min.
- Backups verificados semanalmente (restaurar de verdad, no asumir).

---

## 14. Crítica final

### 14.1 Probabilidad de fallo

Alta. Siendo directos: **como negocio de trading rentable, la probabilidad de fracaso a 12 meses es del orden de 80-95%** (consistente con las tasas de fracaso de traders algorítmicos retail). Como proyecto de construcción de infraestructura, datos y habilidades, la probabilidad de éxito es alta si mantienes disciplina, porque esos entregables no dependen de que el mercado coopere.

### 14.2 Por qué podría fallar

1. **No existe edge** en la estrategia (causa #1, y ninguna ingeniería lo compensa).
2. Overfitting: el backtest miente y le crees.
3. Indisciplina: saltarte gates, subir capital tras rachas, "ajustar" en caliente.
4. Sobre-ingeniería: 6 meses construyendo ecosistema sin un solo trade validado.
5. Fallo operacional en vivo (estado inconsistente, bug de ejecución).
6. Agotamiento: mantener un bot 24/7 en solitario cansa más de lo que parece.
7. Riesgo de contraparte del exchange.

### 14.3 Cómo aumentar la probabilidad de éxito

- Redefinir éxito de la fase 1-4 como: *sistema confiable + datos propios + veredicto estadístico honesto sobre la estrategia*. Eso es 100% alcanzable.
- Gates innegociables entre fases, escritos antes de empezar cada fase.
- Presupuestar la pérdida total del capital inicial como costo de matrícula.
- Un cuaderno de decisiones (ADRs): cada cambio de estrategia/parámetro con fecha y razón. Es tu defensa contra ti mismo.
- Mantener el paralelo: si necesitas ingreso, monetiza las habilidades (ver 14.6), no el bot.

### 14.4 Mentalidad

La de un **ingeniero de confiabilidad y un científico escéptico**, no la de un trader. Tu enemigo no es el mercado: es tu propio sesgo de confirmación. Cada resultado bueno debe ser atacado ("¿dónde está el error?") antes de ser celebrado. Aburrido y sistemático gana a brillante e impulsivo.

### 14.5 Camino más corto a una versión útil

Sprint 0 + Sprint 1 (≈ 3-4 semanas) → backtest walk-forward honesto → decisión informada. En un mes sabrás con datos si la estrategia merece paper trading. Esa velocidad de aprendizaje es la versión útil.

### 14.6 Camino más peligroso a evitar

**Necesidad de dinero + apalancamiento + saltarse validación.** Es la secuencia que destruye cuentas. Si la presión de ingresos crece, el movimiento correcto no es arriesgar más capital: es monetizar lo construido de otra forma (consultoría/desarrollo de infraestructura de datos y bots para terceros, contenido técnico, herramientas SaaS sobre tu propio stack). Ese mercado paga hoy; el alfa, quizá nunca.

---

## 15. Resumen ejecutivo accionable

### Las 10 decisiones más importantes
1. El MVP optimiza aprendizaje y confiabilidad, no ingresos.
2. Estrategia inicial: mean reversion con filtro de régimen, BTC/USDT spot, 1h, long-only, sin apalancamiento.
3. Monolito modular en Python; mismo código en backtest/paper/live.
4. Risk Manager como capa independiente e imposible de bypassear.
5. Gates medibles entre fases; el reloj de paper trading son 8+ semanas y no se acorta.
6. Capital inicial $200-500, keys sin retiro, circuit breakers desde el día uno en vivo.
7. Agentes IA escriben código; nunca tocan riesgo, secretos ni producción; humano revisa todo.
8. Deploy del bot en VPS barato; el rig se pospone a la fase de ML.
9. Validación anti-overfitting: walk-forward, ≤3 parámetros, análisis de sensibilidad.
10. Plan B explícito de monetización de habilidades si el edge no aparece.

### Los 10 primeros pasos
1. Crear el repo con P1. 2. Config con P2. 3. Escribir tú `core/models.py` e `interfaces.py`. 4. `CLAUDE.md` con el protocolo §9.2. 5. Descargar 4 años de BTC/USDT (P3). 6. Estrategia (P4). 7. Risk Manager (P5) con revisión línea a línea. 8. Connectors simulados (P6) y ejecución (P7). 9. Backtester + walk-forward (P8) y primer reporte. 10. Decisión documentada: ¿merece paper trading?

### Los 5 errores más graves a evitar
1. Dinero real sin pasar el gate de paper.
2. Optimizar parámetros sobre los datos de validación.
3. Dar a agentes IA acceso a keys, riesgo o deploy.
4. Construir 15 módulos antes de validar 1 estrategia.
5. Apalancamiento o subir capital por presión de ingresos.

### MVP mínimo
Un proceso Python: collector → mean reversion → risk manager → executor → connector simulado → SQLite/Parquet → logs JSON + alertas Telegram. CLI con `collect`, `backtest`, `run --mode dry-run|paper`.

### Arquitectura mínima viable
Los 6 módulos ✅ de la tabla §5.2 comunicándose solo mediante los tipos de `core/models.py`, con connector intercambiable como único punto de variación entre backtest, paper y live.

### Estrategia recomendada
La de §3.2, tratada como hipótesis a falsificar, con buy&hold como benchmark obligatorio.

### Primer prompt para Codex/Claude Code
El prompt **P1** de la sección 12, tal cual, tras crear el repo vacío y pegar este documento en `docs/plan.md`.

---

## Próximas acciones inmediatas

- [ ] Crear repositorio `trading-ecosystem` y guardar este documento como `docs/plan.md`.
- [ ] Ejecutar P1 (estructura) y P2 (config) con Claude Code/Codex; revisar diffs.
- [ ] Escribir a mano `core/models.py` + `core/interfaces.py` y el `CLAUDE.md` (§9.2).
- [ ] Descargar 4 años de OHLCV BTC/USDT 1h y 1d; correr reporte de calidad de datos.
- [ ] Completar Sprint 1 (P3-P10) en ~2 semanas, un PR por prompt.
- [ ] Correr backtest walk-forward y escribir ADR-002: decisión seguir/iterar sobre la estrategia.
- [ ] Abrir cuenta de exchange con 2FA y keys de solo lectura (sin fondos aún).
- [ ] Definir por escrito tu gate de salida de paper trading (copiar §4.4 y firmarlo con fecha).
- [ ] NO encender el rig; contratar VPS de $5-10 solo cuando empiece la fase de paper 24/7.
- [ ] Verificar tus obligaciones tributarias en Chile antes de la Fase 4.

*Fin del documento.*
