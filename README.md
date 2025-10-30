# mini-matching-engine
Event based mini matching engine


A lightweight asynchronous **order matching engine** built with Python & NATS.  
Designed to simulate exchange order flows with simple pub/sub messaging.

### Overview

The engine listens to incoming order events via **NATS**, processes matching logic based on price–time priority, and outputs executed **trade events**.

Components:
- **pusher** → publishes orders to NATS (`orders.in`)
- **engine** → consumes orders, matches them, and publishes trades (`trades.out`)
- **common** → shared modules for configuration, models, and broker utilities

**Matching Logic:**
- Standard *price–time priority* rule  
- Buy crosses if `best_ask.price <= incoming_buy.price`  
- Sell crosses if `best_bid.price >= incoming_sell.price`  
- Trade price = maker order’s price  
- Supports `create`, `amend`, and `cancel` order types
- Supports multi-symbol based flow

### Configuration

All runtime configuration is stored in **`settings.yaml`**.

### Configuration

| Key | Example Value | Description |
|------|----------------|-------------|
| **nats.url** | `"nats://nats:4222"` | NATS server connection URL. Use the `nats` service name in Docker. |
| **nats.orders_subject** | `"orders.in"` | Subject where pusher publishes incoming orders. |
| **nats.consume_subject** | `"orders.in"` | Subject consumed by the matching engine (usually same as `orders_subject`). |
| **nats.trades_subject** | `"trades.out"` | Subject where engine publishes matched trade events. |
| **nats.connection.reconnect** | `true` | Automatically reconnect to NATS if the connection is lost. |
| **nats.connection.max_reconnect_attempts** | `5` | Maximum number of reconnection retries. |
| **nats.connection.reconnect_wait_ms** | `500` | Wait time between reconnect attempts in milliseconds. |
| **nats.connection.timeout_ms** | `2000` | Timeout for the initial connection in milliseconds. |
| **engine.input_path** | `"data/sample.ndjson"` | Path to the input `.ndjson` file containing sample orders (used by the pusher). |
| **engine.output_path** | `"data/trades.ndjson"` | Path where the engine writes matched trade results. |

### Example `settings.yaml`

```yaml
nats:
  url: "nats://nats:4222"
  orders_subject: "orders.in"
  consume_subject: "orders.in"
  trades_subject: "trades.out"
  connection:
    reconnect: true
    max_reconnect_attempts: 5
    reconnect_wait_ms: 500
    timeout_ms: 2000

engine:
  input_path: "data/sample.ndjson"
  output_path: "data/trades.ndjson"
  
```


### Run with Docker Compose

### Build & Start
```bash
docker compose up --build
```

### Logs
```bash
docker compose logs -f engine
docker compose logs -f pusher
```

### Local Development

You can also run the matching engine locally with **Poetry** — no Docker required.

---

#### Install Dependencies:

Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed (required version is 2.1.3) : 

```bash
poetry install
```
This will create a virtual environment and install all dependencies defined in pyproject.toml

#### Install NATS:

You can install NATS from the official website: [NATS](https://nats.io/download/)

Or install it via **Homebrew** (macOS):

```bash
brew install nats-server
```

Once installed, start a local NATS server:
```bash
nats-server -p 4222
```
This will run NATS on port 4222 (the default). 
You should change your url variable in setting.yaml file as url: "nats://localhost:4222"

#### Run the Publisher (Pusher):

The **Pusher** publishes sample orders from `data/sample.ndjson` to NATS.  
It simulates a live order flow that the matching engine will consume.

Run it with:

```bash
poetry run python -m src.pusher.main
```
#### Run the Engine (Consumer and Matcher):
**The Engine** listens for incoming order messages from NATS,
matches buy/sell orders based on price–time priority, and writes resulting trades to file.

Run it in a separate terminal:
```bash
poetry run python -m src.engine.main
```

You can stop the engine anytime with:
```bash
Ctrl\Cmd + C
```

Trade orders will be located in engine/data directory.