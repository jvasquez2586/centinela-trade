# ADR-003: Exchanges y entornos de ejecución

- **Estado:** Aceptada
- **Fecha:** 2026-10-10 (aceptada 2026-10-18)
- **Relacionado con:** docs/plan.md §3, §4, §8, §9, §10; ADR-001 (stack)

## Contexto

El bot MVP opera BTC/USDT spot, 1h, long-only, con 2-8 señales/mes y $200-500 de capital en Fase 4.
Con esa frecuencia, los rate limits no son una restricción relevante; las comisiones sí, porque
una estrategia de mean reversion con stop de -2,5% y objetivos de 1-3% no tolera costos de ida
y vuelta altos. El operador reside en Chile.

## Decisión

| Rol | Plataforma | Keys / credenciales |
|---|---|---|
| Datos históricos (Fase 1-2) | Binance, endpoints públicos | Ninguna |
| Integración / CI | Binance Spot Testnet (testnet.binance.vision) | Keys de testnet (login GitHub) |
| Paper trading (Fase 3) | Connector paper propio (P6) como fuente de verdad + connector live (ccxt) apuntado a Binance Demo Mode (demo-api.binance.com) para validar el ciclo de órdenes real | Keys de Demo Mode |
| Live (Fase 4) | Binance spot, en la subcuenta `tradebot001` (correo virtual) | Key de subcuenta: lectura + spot trading, sin retiro, restringida por IP del VPS |
| Respaldo live | OKX spot | Cuenta verificada, sin keys hasta que se necesite |
| Sandbox de agentes IA | Kraken CLI en modo `market,account,paper` | Ninguna con permisos de trading |

### Por qué Binance como principal
- Comisión spot más baja disponible (0,10%; 0,075% pagando con BNB). Verificado 2026-10-10.
- Depósito en CLP desde bancos chilenos.
- Mayor liquidez en BTC/USDT y mejor soporte en ccxt.
- Demo Mode con precios y libro similares al live: permite probar el connector live sin dinero.

### Por qué Demo Mode y no solo Testnet para Fase 3
- Testnet: precios y libro independientes del mercado real; saldos se reinician cada mes.
- Demo Mode: precios similares al live, mismas funciones que producción.
- El connector paper propio sigue siendo la fuente de verdad del gate §4.4 (fills pesimistas).
  Demo Mode se usa para verificar que `live_ccxt.py` maneja estados, rechazos y cancelaciones reales.
- Advertencia oficial de Binance: que una estrategia funcione en Demo Mode no implica que funcione en live.

## Alternativas consideradas
- **OKX:** comisiones equivalentes (0,08% maker / 0,10% taker). Queda como respaldo.
- **Kraken:** mejor tooling para agentes (CLI + MCP con paper), pero comisión base 0,25%/0,40% o más
  tras su cambio de tarifas de julio 2026. Descartado para ejecución; se usa como sandbox de agentes.
- **Buda.com:** local y con CLP, pero comisiones de 0,1-0,4% maker / 0,3-0,8% taker en Buda Pro.
  Descartado para el bot.
- **Bitget, BingX, Bitunix:** orientados a derivados; Bitget con incidente de seguridad (sept. 2026). Descartados.

## Consecuencias
- Binance y OKX no están inscritos en el RPSF de la CMF: no hay protección de la normativa chilena.
  Mitigación: en el exchange solo vive el capital del bot; el resto de los fondos fuera.
- Binance bloquea IPs de EE.UU. (HTTP 451). El VPS de producción debe estar en Europa y pasar
  `scripts/check_binance_env.py` antes de configurarse.
- Binance no reporta al SII: el log de auditoría del bot es el registro tributario. Antes de Fase 4
  se agrega un export de operaciones (fecha, par, lado, cantidad, precio, fee).
- El connector es ccxt: cambiar a OKX es un cambio de configuración más pruebas, no una reescritura.

## Reglas de credenciales
1. Ningún agente IA ve ni usa keys de Demo Mode, subcuenta live u OKX (plan §9.1).
2. Keys de Testnet: permitidas solo en CI y en la máquina de desarrollo.
3. Keys de live: solo en el VPS, creadas al iniciar Fase 4, nunca antes.
4. Rotación cada 90 días o ante cualquier sospecha.
5. Ningún MCP con permisos de trading conectado a una cuenta con fondos.

## Revisión
Revisar esta decisión si: cambian las comisiones de Binance u OKX, Binance o la CMF cambian las
condiciones para residentes en Chile, el VPS no logra conectarse, o antes de iniciar Fase 4
(revalidar comisiones y estado regulatorio).

## Notas de implementación (2026-10-18)
- Keys de Demo Mode: Binance no permite editar sus permisos (vienen con lectura, spot y futuros). Aceptable porque son fondos ficticios; el bot solo usa endpoints spot.
- Keys de Testnet: permisos TRADE, USER_DATA y USER_STREAM.
- Verificación: `scripts/check_binance_env.py` (sandbox) pasó en los tres entornos desde Ubuntu.
