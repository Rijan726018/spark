# NEXUS AI — ARCHITECTURE.md
**The Shared Brain. Gemini writes here. Claude reads here.**

---

## ORCHESTRATION RULES
1. **Gemini (Master Architect)** — scans the codebase and writes specs into this file.
2. **Claude (Executor)** — reads this file before touching any code. Never changes this doc.
3. **Error Feedback Loop** — if Claude hits an error, copy it back to Gemini. Gemini updates the spec here. Claude re-reads and re-executes.
4. **Golden Rule** — one source of truth. If ARCHITECTURE.md and the code disagree, the code is wrong.

---

## CURRENT SYSTEM STATE
*Last verified: 2026-04-14 by Claude (executor)*

### Stack Overview
```
React (Vite) ──HTTP/WS──► FastAPI (uvicorn) ──.delay()──► Redis ──► Celery Worker
localhost:5173              localhost:8000       localhost:6379
```

### Directory Map
```
c:\Users\rijan\Claude\
├── ARCHITECTURE.md              ← THIS FILE (shared brain)
│
├── server/
│   └── main.py                  ← FastAPI app (the entire backend server)
│       PORT: 8000
│       CORS: allow_origins=["*"]
│
├── backend/
│   └── router/
│       ├── celery_app.py        ← Celery instance (broker + backend = redis://localhost:6379/0)
│       ├── execution.py         ← @celery_app.task execute_order(user_account_id, symbol, integer_qty, action)
│       ├── allocator.py         ← process_master_signal(str) — fans out to sub-accounts via execute_order.delay()
│       └── auth.py              ← get_tradovate_token() — Redis-cached OAuth token
│
└── frontend/
    └── src/
        ├── main.jsx
        ├── index.css
        ├── views/
        │   └── Dashboard.jsx    ← Full terminal layout (TopBar, ChartHeader, AlgoSidebar, TradingViewChart, AlgoDetails, PammPanel, TradeLog)
        ├── components/
        │   ├── AlgoSidebar.jsx
        │   ├── TradingViewChart.jsx
        │   ├── TradeLog.jsx
        │   └── ExecutionChart.jsx
        └── hooks/
            └── useMarketData.js ← WebSocket hook (connects to /ws/market)
```

---

## LIVE API CONTRACT
*server/main.py — all routes currently implemented*

### REST Endpoints
| Method | Path | Returns | Notes |
|--------|------|---------|-------|
| GET | `/api/algos` | `Algo[]` | 525 configs loaded from `algo_configs.py` |
| GET | `/api/algo/{id}` | `Algo` | Zero-padded ID (e.g. "001") |
| GET | `/api/bars/{symbol}` | `{symbol, tf, bars, synthetic?}` | NT bridge → CSV → synthetic fallback |
| GET | `/api/trades/{algo_id}` | `{algo_id, trades, synthetic?}` | CSV → synthetic fallback |
| GET | `/api/account` | `{balance, pnl, daily_pnl, ...}` | Mock data currently |
| GET | `/api/positions` | `{positions[]}` | Mock data currently |
| GET | `/api/status` | `{server, version, algo_count, ...}` | Health check |
| GET | `/api/backtest/{algo_id}` | `{stats, series[]}` | Synthetic equity curve |
| **POST** | **`/api/trade`** | `{status, signal, message}` | **PAMM gateway — new** |
| **GET** | **`/api/task/{task_id}`** | `{task_id, status, result, ready}` | **Celery result poll — new** |

### WebSocket — `ws://localhost:8000/ws/market`
Message types the server **broadcasts**:
```json
{ "type": "bar",        "symbol": "ES", "tf": "5m", "bar": { "time":int, "open":float, "high":float, "low":float, "close":float, "volume":int } }
{ "type": "execution",  "algo_id": "001", "symbol": "ES", "side": "BUY"|"SELL", "price": float, "qty": int, "time": int }
{ "type": "status",     "nt_connected": bool, "broker_connected": bool, "active_algos": int, "timestamp": int }
{ "type": "pamm_signal","symbol": str, "action": str, "quantity": float, "signal": str, "timestamp": int }
```
Messages the client **sends**:
```json
{ "type": "ping" }
{ "type": "subscribe", "symbol": "ES" }
```

### POST /api/trade Payload
```json
{ "symbol": "ES", "action": "Buy", "quantity": 2.0 }
```
Response:
```json
{ "status": "queued", "signal": "Buy 2.0 ES Contract at Market", "message": "..." }
```

---

## PAMM ALLOCATOR LOGIC
*backend/router/allocator.py*

**Registered sub-accounts (mock):**
| user_id | balance | pool_weight |
|---------|---------|-------------|
| 1 | $5,000 | 2.5% |
| 2 | $15,000 | 7.5% |
| 3 | $30,000 | 15.0% |
| 4 | $50,000 | 25.0% |
| 5 | $100,000 | 50.0% |
**Total pool: $200,000**

**ES → MES conversion rule:** `math.floor(fractional_es * 10)`
Risk protocol: floor() not round(). If allocation < 1.0 MES → skip (protect from micro-leverage).

**Signal format:** `"Buy 2 ES Contract at Market"`
Parser: `parts[0]=action, parts[1]=quantity (float), parts[2]=symbol`

---

## FRONTEND DATA FLOW
*frontend/src/hooks/useMarketData.js*

```
WebSocket(ws://localhost:8000/ws/market)
    │
    ├── type="bar"       → setBars({ [symbol]: Bar[] })  +  setLastBar({ [symbol]: Bar })
    ├── type="execution" → setTrades({ [algoId]: Trade[] })  +  setAllTrades(Trade[])
    ├── type="status"    → setNtConnected / setBrokerConnected / setActiveAlgos
    └── type="pamm_signal" → currently UNHANDLED (next feature candidate)
```

Constants:
- `MAX_BARS_PER_SYMBOL = 2000`
- `MAX_TRADES_PER_ALGO = 500`
- Reconnects with exponential backoff: 1s → 30s max

**REST seeding (Dashboard.jsx):**
- On algo select → `GET /api/bars/{symbol}?limit=500&tf={tf}` → `seedBars()`
- On algo select → `GET /api/trades/{id}?limit=100` → `seedTrades()`
- Every 30s → `GET /api/account`

---

## DASHBOARD LAYOUT
*frontend/src/views/Dashboard.jsx — 820 lines*

```
┌──────────────────────────────────────────────────────────┐
│  TopBar (44px) — logo | WS/NT/BROKER dots | P&L | clock  │
├──────────┬───────────────────────────────┬───────────────┤
│AlgoSidebar│ ChartHeader                  │ AlgoDetails   │
│(fixed w) │ TradingViewChart              │ (200px fixed) │
│          │ [chart-wrapper flex:1]        │               │
├──────────┴───────────────────────────────┴───────────────┤
│  PammPanel (62px) — PAMM ROUTER | SYMBOL | ACTION | QTY  │  ← NEW
│  [pamm-panel] id="pamm-execute-btn"                      │
├──────────────────────────────────────────────────────────┤
│  TradeLog (execution table, scrollable)                   │
└──────────────────────────────────────────────────────────┘
```

**Key state in Dashboard:**
- `algos[]` — fetched from `/api/algos`, retried with backoff
- `selectedAlgo` — drives chart symbol + details panel
- `account` — `{balance, daily_pnl}` polled every 30s
- `chartHeight` — measured via ResizeObserver on `#chart-wrapper`
- `bars/trades/allTrades/lastBar` — all from `useMarketData()`

---

## KNOWN LIMITATIONS / OPEN WORK

| # | Area | Status | Notes |
|---|------|--------|-------|
| 1 | `pamm_signal` WS event | Unhandled in `useMarketData.js` | Could update trade log in real-time |
| 2 | Task ID return | `POST /api/trade` doesn't return individual Celery task IDs | `process_master_signal()` fires `.delay()` internally |
| 3 | Real Tradovate auth | Mock token in `auth.py` | `.env` file needed for production |
| 4 | Account data | Hardcoded in `GET /api/account` | Needs real broker balance feed |
| 5 | `GET /api/task/{id}` | Implemented but no UI to poll it | Frontend could show per-task status |
| 6 | NT Broker connection | Mock only (`ib_insync` not installed) | `engines/broker.py` present |

---

## BOOT SEQUENCE
```powershell
# Tab 1 — Message broker
docker run -d -p 6379:6379 --name nexus-redis redis

# Tab 2 — Celery worker
py -m celery -A backend.router.celery_app worker --loglevel=info --pool=solo

# Tab 3 — FastAPI gateway
py -m uvicorn server.main:app --reload --port 8000

# Tab 4 — React dashboard
cd frontend && npm run dev
```

---

## FEATURE SPECS
*Written by Gemini (Architect). Executed by Claude (Worker).*

### SPEC: Real-Time TradingView Charting System (Tradovate ES Tick Data)

#### 1. System Overview
The objective is to establish a low-latency, real-time charting system streaming E-mini S&P 500 (ES) tick data directly from Tradovate to the React frontend.
**Data Flow Architecture:**
- **Tradovate WebSocket:** Connects to Tradovate's market data WebSocket using a valid OAuth token to subscribe to raw `ES` tick/quote events.
- **Redis (Message Broker & Cache):** The raw tick data is ingested by a background Python daemon and immediately published to a Redis Pub/Sub channel (e.g., `market_data:ES`). Redis also handles short-lived OAuth token caching to prevent Tradovate API rate limits.
- **FastAPI (API Gateway):** A FastAPI WebSocket endpoint (`/ws/prices`) subscribes to the Redis `market_data:ES` channel and broadcasts the incoming tick data asynchronously to all connected React clients.
- **React (Frontend):** Subscribes to the FastAPI WebSocket, parses the incoming payloads, and seamlessly updates the `lightweight-charts` instance on the dashboard without triggering expensive DOM re-renders.

#### 2. The Data Daemon
**File:** `backend/data_feed.py`
This standalone background process is responsible for maintaining the upstream Tradovate connection.
- **Token Management:** Securely retrieves the Tradovate OAuth token. The token must be cached in Redis with an explicit TTL (Time-To-Live) matching Tradovate's expiry. Prior to reconnecting or refreshing the WebSocket, the daemon checks Redis for a valid token, requesting a new one only if the cache expires.
- **WebSocket Client:** Uses `websockets` or `asyncio` to connect to Tradovate's Market Data URI.
- **Data Ingestion:** Subscribes to tick data for the ES symbol. Upon receiving a frame, parses it into an internal standardized JSON schema (Tick: `{symbol, timestamp, price, volume, bid, ask}`).
- **Broadcasting:** Emits the standardized JSON string to the Redis Pub/Sub channel `market_data_stream`.

#### 3. The API Gateway
Defines a dedicated high-throughput WebSocket route in the FastAPI server.
- **Route:** `@app.websocket("/ws/prices")` (located in `server/main.py` or a dedicated router).
- **Behavior:** 
  - On client connection: Accepts the WebSocket upgrade and runs an async loop subscribing to the Redis `market_data_stream` Pub/Sub channel.
  - On incoming Redis message: Parses the payload and forwards the following standard schema to the React client:
    ```json
    {
      "type": "tick",
      "symbol": "ES",
      "data": {
        "time": 1684345200000,
        "price": 4152.25,
        "volume": 5
      }
    }
    ```
  - On disconnect: Gracefully cleans up the Redis subscription and drops the client from the active connection pool.

#### 4. The Frontend
The charting UI will be built utilizing TradingView's `lightweight-charts` for optimal canvas rendering of high-frequency tick data.
- **Component (`TradingViewChart.jsx` or similar):**
  - **Initialization:** `useEffect` hook to mount a `createChart` instance on a ref container. Configured with a `CandlestickSeries` (for historical context) and a `LineSeries` or dynamically populated last-price line for live ticks.
  - **Data Intake:** Integrates a custom WebSocket hook (`usePriceData.js` or expanding `useMarketData.js`).
  - **Update Logic:** When a `tick` payload arrives via the WebSocket, it invokes `series.update({ time: tick.time, value: tick.price })`. This mutable update ensures real-time movement without triggering React component re-renders.
  - **Cleanup:** Ensures chart `.remove()` and WebSocket disconnection on component unmount.

#### 5. The Worker Instructions
@claude: Follow this strictly numbered execution plan to implement the system:

1. **Phase 1: Build the Data Daemon**
   - Create `backend/data_feed.py`.
   - Implement the Tradovate OAuth retrieval and Redis caching logic (ensure you include a Redis TTL mechanism to manage token lifecycles).
   - Implement the async Tradovate WebSocket client that ingests ES ticks and publishes them to the Redis `market_data_stream` channel.

2. **Phase 2: Establish the API Gateway**
   - In `server/main.py` (or a relevant WebSocket router), add the new async route: `@app.websocket("/ws/prices")`.
   - Implement the Redis Pub/Sub listener loop within the endpoint that forwards tick messages to the connected React clients using the defined JSON schema.

3. **Phase 3: Connect the Frontend Charting**
   - Ensure `lightweight-charts` is installed in the frontend payload.
   - Modify the frontend WebSocket hook (or create a new `usePriceData.js`) to connect to `ws://localhost:8000/ws/prices`.
   - Update `frontend/src/components/TradingViewChart.jsx` to render the `lightweight-charts` instance and directly process the incoming tick stream utilizing `.update()` functionality.
