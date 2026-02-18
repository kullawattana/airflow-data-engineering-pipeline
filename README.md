# Airflow Data Engineering Pipeline

A data engineering pipeline built with **Apache Airflow** (via Astronomer) that automatically collects cryptocurrency price data from the **Binance API**, stores it in **MongoDB Atlas**, computes periodic average prices, and visualizes the results in Jupyter Notebooks.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Process Flowchart](#process-flowchart)
- [Project Structure](#project-structure)
- [DAGs Description](#dags-description)
- [Visualization](#visualization)
- [Setup & Installation](#setup--installation)
- [Airflow Connections Required](#airflow-connections-required)

---

## Architecture Overview

```
┌─────────────────┐      ┌──────────────────────┐      ┌────────────────────────┐
│   Binance API   │─────▶│   Apache Airflow      │─────▶│   MongoDB Atlas (BIDB) │
│  (crypto prices)│      │   (Astronomer Runtime) │      │   - get_binance        │
└─────────────────┘      └──────────────────────┘      │   - average_prices     │
                                    │                   │   - prices_YYYY_MM_DD  │
                                    │                   │   - collections_prices │
                          ┌─────────▼──────────┐        └────────────────────────┘
                          │  Scheduler triggers │                   │
                          │  every 15 min and   │                   │
                          │  every 3 hours      │       ┌───────────▼────────────┐
                          └─────────────────────┘       │  Jupyter Notebooks     │
                                                        │  (Visualization /      │
                                                        │   matplotlib charts)   │
                                                        └────────────────────────┘
```

**Technology Stack:**

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Orchestration | Apache Airflow 2.x (Astronomer Runtime 11.7.0) |
| Containerization | Docker (via `astro dev`)         |
| Data Source   | Binance REST API (v3 ticker)        |
| Storage       | MongoDB Atlas (cloud)               |
| Visualization | Jupyter Notebook + matplotlib       |
| Language      | Python 3.x                          |

---

## Process Flowchart

The pipeline consists of two automated stages running on different schedules.

### Stage 1 — Data Ingestion (every 15 minutes, 6 AM–11 PM)

```
DAG: get_binance_price_every_15_minutes
Schedule: */15 6-23 * * *

┌─────────────────────────────────────────────────────────┐
│                                                         │
│  START (every 15 minutes from 06:00 to 23:00)           │
│     │                                                   │
│     ▼                                                   │
│  [Task 1] get-currency-from-binance                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │  SimpleHttpOperator                             │    │
│  │  GET /api/v3/ticker                             │    │
│  │  symbols: BTCUSDT, BNBUSDT, ETHUSDT             │    │
│  │  windowSize: 15m                                │    │
│  │                                                 │    │
│  │  Returns: openPrice, highPrice, lowPrice,       │    │
│  │           lastPrice, volume, quoteVolume, etc.  │    │
│  └─────────────────────────────────────────────────┘    │
│     │                                                   │
│     │  (XCom push → pass JSON result to next task)      │
│     ▼                                                   │
│  [Task 2] upload-to-mongodb-db                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  PythonOperator                                 │    │
│  │  MongoHook → connect to MongoDB Atlas           │    │
│  │  Database : BIDB                                │    │
│  │  Collection: get_binance                        │    │
│  │  Action: insert_one({ "data": <raw_json> })     │    │
│  └─────────────────────────────────────────────────┘    │
│     │                                                   │
│     ▼                                                   │
│  END                                                    │
└─────────────────────────────────────────────────────────┘
```

### Stage 2 — Aggregation & Storage for Visualization (every 3 hours)

```
DAG: get_binance_price_every_3_hours_for_visualization
Schedule: 5 */3 * * *

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  START (every 3 hours at :05)                                │
│     │                                                        │
│     ▼                                                        │
│  [Task 1] compute_average_prices_of_binance                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  PythonOperator                                      │    │
│  │                                                      │    │
│  │  Step A: Read all raw records from                   │    │
│  │          BIDB.get_binance (collected by Stage 1)     │    │
│  │                                                      │    │
│  │  Step B: For each record, parse JSON data field      │    │
│  │          and group lastPrice values by symbol        │    │
│  │                                                      │    │
│  │  Step C: Compute average lastPrice per symbol        │    │
│  │          avg = sum(prices) / count(prices)           │    │
│  │          Result: { BTCUSDT: x, ETHUSDT: y, ... }    │    │
│  │                                                      │    │
│  │  Step D: Build result document                       │    │
│  │          { timestamp: <ISO UTC>, avg_price: {...} }  │    │
│  │                                                      │    │
│  │  Step E: Write to MongoDB                            │    │
│  │    ├── BIDB.average_prices       (rolling store)     │    │
│  │    ├── BIDB.prices_YYYY_MM_DD_HH_MM (point-in-time) │    │
│  │    └── BIDB.collections_prices_date_times (index)   │    │
│  └──────────────────────────────────────────────────────┘    │
│     │                                                        │
│     ▼                                                        │
│  END                                                         │
└──────────────────────────────────────────────────────────────┘
```

### End-to-End Pipeline View

```
Binance API
    │
    │  GET ticker (15-min window)
    ▼
[Airflow - Stage 1] ──────────────────────────▶ MongoDB: BIDB.get_binance
Every 15 min (06:00–23:00)                      (raw price snapshots)
                                                         │
                                                         │  (read all accumulated records)
                                                         ▼
                                            [Airflow - Stage 2]
                                            Every 3 hours at :05
                                                         │
                                          ┌──────────────▼──────────────┐
                                          │  Compute average prices      │
                                          │  per symbol per time window  │
                                          └──────────────┬──────────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              ▼                          ▼                          ▼
                    BIDB.average_prices      BIDB.prices_YYYY_MM_DD_HH_MM  BIDB.collections_
                    (all-time rolling)       (per-batch snapshot)           prices_date_times
                              │                                                      │
                              └──────────────────────┬───────────────────────────────┘
                                                     ▼
                                          Jupyter Notebook
                                          ┌─────────────────────────────┐
                                          │  Read from MongoDB           │
                                          │  Build pandas DataFrame      │
                                          │  Plot time-series chart      │
                                          │  (BTCUSDT / ETHUSDT / BNBUSDT│
                                          │   vs Time using matplotlib)  │
                                          └─────────────────────────────┘
```

---

## Project Structure

```
airflow-data-engineering-pipeline/
│
├── README.md                          # This file
│
├── airflow-pipeline/                  # Astronomer Airflow project
│   ├── Dockerfile                     # Astro Runtime 11.7.0 base image
│   ├── requirements.txt               # Python dependencies (apache-airflow-providers-mongo)
│   ├── packages.txt                   # OS-level packages
│   │
│   └── dags/                          # Airflow DAG definitions
│       ├── assignment_dag_get_binance_api.py           # Stage 1: Fetch & store raw prices
│       ├── assignment_dag_get_mongodb_for_visualization.py  # Stage 2: Aggregate for viz
│       ├── assignment_dag_get_mongodb.py               # Alternative aggregation DAG
│       ├── dag_get_currency_binance.py                 # Manual currency load DAG
│       ├── line_notification.py                        # LINE notification DAG
│       ├── line_notification_by_tag_dag.py             # LINE notification (by tag) DAG
│       ├── tutorial_simple_dag.py                      # Tutorial: basic DAG
│       ├── tutorial_dag_with_jinja_template.py         # Tutorial: Jinja templating
│       ├── tutorial_dag_with_send_email.py             # Tutorial: email notification
│       ├── my_astronauts_dag.py                        # Tutorial: Open Notify API
│       └── example_dag.py                              # Example DAG
│
├── visualization/                     # Jupyter Notebooks for data exploration & charts
│   ├── get_binance_data_from_mongoDB.ipynb
│   ├── get_binance_data_from_mongoDB_with_visualization.ipynb   # Main viz notebook
│   ├── visualization_get_binance_data_from_mongoDB.ipynb
│   └── poc_visualization_get_binance_data_from_mongoDB.ipynb
│
└── workshop-main/                     # Workshop reference materials
    ├── de/
    │   ├── Lab1/                      # Data format labs (JSON, Avro, Parquet)
    │   └── Lab2/                      # DAG labs (mirrors dags/ folder)
    └── README.md
```

---

## DAGs Description

### 1. `get_binance_price_every_15_minutes`
**File:** [airflow-pipeline/dags/assignment_dag_get_binance_api.py](airflow-pipeline/dags/assignment_dag_get_binance_api.py)

| Property | Value |
|----------|-------|
| Schedule | `*/15 6-23 * * *` (every 15 min, 6 AM–11 PM) |
| Database | `BIDB` |
| Collection | `get_binance` |

**Tasks:**

| Task ID | Operator | Description |
|---------|----------|-------------|
| `get-currency-from-binance` | `SimpleHttpOperator` | Calls Binance API for BTC, ETH, BNB mini-ticker data with a 15-minute window |
| `upload-to-mongodb-db` | `PythonOperator` | Reads XCom result from Task 1 and inserts the raw JSON into MongoDB |

**Dependencies:** `get-currency-from-binance` → `upload-to-mongodb-db`

---

### 2. `get_binance_price_every_3_hours_for_visualization`
**File:** [airflow-pipeline/dags/assignment_dag_get_mongodb_for_visualization.py](airflow-pipeline/dags/assignment_dag_get_mongodb_for_visualization.py)

| Property | Value |
|----------|-------|
| Schedule | `5 */3 * * *` (every 3 hours at :05) |
| Database | `BIDB` |
| Collections written | `average_prices`, `prices_YYYY_MM_DD_HH_MM`, `collections_prices_date_times` |

**Tasks:**

| Task ID | Operator | Description |
|---------|----------|-------------|
| `compute_average_prices_of_binance` | `PythonOperator` | Reads all raw records from `get_binance`, computes average `lastPrice` per symbol, and writes timestamped aggregates to MongoDB |

---

### 3. `get_binance_price_every_3_hours` (alternative)
**File:** [airflow-pipeline/dags/assignment_dag_get_mongodb.py](airflow-pipeline/dags/assignment_dag_get_mongodb.py)

Similar aggregation DAG using a direct `pymongo` connection (no Airflow hook). Reads from `get_binance_price_collection` and writes to `get_average_binance_price_collection` in the `MyDB` database.

---

### 4. `load_currency_data`
**File:** [airflow-pipeline/dags/dag_get_currency_binance.py](airflow-pipeline/dags/dag_get_currency_binance.py)

| Property | Value |
|----------|-------|
| Schedule | Manual trigger only (`None`) |
| Collection | `currency_collection` |

Fetches historical currency data from a configured HTTP connection and stores it in MongoDB.

---

## Visualization

The Jupyter Notebooks in [visualization/](visualization/) connect to MongoDB Atlas, retrieve average price data, and plot time-series charts using **matplotlib**.

**Main workflow inside the notebook:**

```python
# 1. Connect to MongoDB Atlas
client = MongoClient(uri)
db = client['BIDB']

# 2. Read average_prices collection
all_data = db.average_prices.find()

# 3. Build a pandas DataFrame
df = pd.DataFrame(data_list)
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df.set_index('datetime', inplace=True)

# 4. Plot
plt.plot(df.index, df['BTCUSDT'], label='BTCUSDT')
plt.plot(df.index, df['ETHUSDT'], label='ETHUSDT')
plt.plot(df.index, df['BNBUSDT'], label='BNBUSDT')
plt.show()
```

The chart displays **BTCUSDT**, **ETHUSDT**, and **BNBUSDT** average prices over time.

---

## Setup & Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Astronomer CLI](https://docs.astronomer.io/astro/cli/install-cli) (`astro`)

### Start Airflow locally

```bash
cd airflow-pipeline
astro dev start
```

This spins up 4 Docker containers:

| Container  | Description                          | Port  |
|------------|--------------------------------------|-------|
| Postgres   | Airflow metadata database            | 5432  |
| Webserver  | Airflow UI                           | 8080  |
| Scheduler  | Monitors and triggers tasks          | —     |
| Triggerer  | Handles deferred tasks               | —     |

Access the Airflow UI at `http://localhost:8080` (username: `admin`, password: `admin`).

### Stop Airflow

```bash
astro dev stop
```

---

## Airflow Connections Required

Configure these connections in the Airflow UI under **Admin → Connections**:

| Connection ID  | Type  | Description                         |
|----------------|-------|-------------------------------------|
| `binance_api`  | HTTP  | Base URL: `https://api.binance.us`  |
| `mongo_default`| MongoDB | MongoDB Atlas connection string   |
