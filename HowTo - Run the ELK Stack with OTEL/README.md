# Run the ELK Stack with OpenTelemetry (OTEL)

This recipe runs Elasticsearch, Kibana, an **EDOT Collector** (Elastic Distribution of OpenTelemetry
Collector) and a small **Python (Flask) shop app**. The app runs under **gunicorn** and uses
**PostgreSQL**, **Redis** and **Elasticsearch** (product search), so it behaves like a real multi-tier
application. It is instrumented with the OpenTelemetry SDK: every call produces **logs, metrics and
traces**, which are sent via OTLP to the collector and written natively (OTel mapping mode) to
Elasticsearch. Because every query and Redis command is traced, Kibana can show the **dependencies**
of the app (service map / dependencies view). The app also reports the `container.id` and `host.name` it
runs on, and the collector scrapes CPU/memory/network of every container (`docker_stats`) plus the
PostgreSQL and Redis metrics themselves, so a service can be tied to its infrastructure.

```
                         OTLP (logs, metrics, traces)
 curl ─► app (gunicorn ─────────────────────────────┐
          2 workers x 4 threads)                     ▼
           │  SQL            │ commands        edot-collector ──HTTPS──► es01 ◄── kibana
           ▼                 ▼                  ▲   ▲
        postgres           redis ───────────────┘   │   scrapes infra metrics
           └────────────────────────────────────────┘   (postgresql, redis, docker_stats)
```

| File | Purpose |
|------|---------|
| `docker-compose.yml` | `setup` (certs), `es01`, `kibana`, `edot-collector`, `postgres`, `redis`, `app` |
| `otel-collector.yml` | EDOT Collector pipelines: OTLP + `postgresql`/`redis`/`docker_stats` receivers → `elasticsearch/otel` exporter |
| `app/app.py` | The sample app (Flask, psycopg, redis-py, elasticsearch-py, traces/metrics/logs set up with the OTel SDK) |
| `app/gunicorn.conf.py` | gunicorn settings (bind, workers, threads, access log) |
| `postgres/init.sql` | Creates the tables `products` (50 sample rows) and `orders` on the first start |
| `.xrc` | `x_call`, `x_load`, `x_otel_status` on top of the common `x_*` commands |

The EDOT Collector is the `elastic-agent` image started in OpenTelemetry mode (`elastic-agent otel
--config ...`); no Fleet is involved.

01. Change into the HowTo directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run the ELK Stack with OTEL"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (stack version, ports, memory limits, PostgreSQL credentials)

03. List the available shorthands, then start the stack (the app image is built on the first run)

        ubuntu~$> x_ls
        ubuntu~$> x_up

    The startup order is `es01` and `postgres`/`redis` → `kibana` + `edot-collector` (healthy once
    OTLP port `4317` listens) → `app`.

04. Call the app. Every endpoint produces a trace (server span plus client spans for each PostgreSQL
    query and Redis command), metrics and logs:

    Endpoint | What it does | Signals worth a look
    ---------|--------------|---------------------
    `GET /` | load + process data (simulated work) | spans `load-data`, `process-data`
    `GET /products` | `SELECT` from PostgreSQL | `postgresql` client spans
    `GET /products/<id>` | `SELECT` by id, `404` for ids > 50 | warning log, 4xx transactions
    `GET /search?q=..` | Redis cache lookup (10 s TTL); on a miss a `match` query against the Elasticsearch index `products` (filled from PostgreSQL on the first search) + `SETEX` | `elasticsearch` client span, `app.cache.requests{result=hit\|miss}`
    `GET /login?user=..` | Redis session (`SETEX`), `401` + failed-attempt counter (`INCR`) for users starting with `bad` | warning log
    `POST /orders` | `INSERT` into PostgreSQL, `RPUSH` to a Redis queue; ~10% fail with a real foreign key violation (`500`) | `app.orders.created`, `app.orders.value`, `app.queue.depth`
    `POST /checkout` | `DECR` stock in Redis, call an external payment provider (simulated): ~15% `402`, ~5% timeout `504`, `LPOP` from the queue | external dependency `payment-provider`
    `GET /slow` | `SELECT pg_sleep(0.8-2s)` | slow database spans, latency outliers
    `GET /error` | always fails with an exception | failed span with exception, error log

    Common metrics: `app.requests` (by endpoint, method, status), `app.requests.inflight`,
    `app.work.duration` (per step).

        ubuntu~$> x_call                  # same as: curl http://localhost:8000/
        ubuntu~$> x_call products/7       # any path, e.g. products/7 or error
        ubuntu~$> x_load                  # 50 random calls over all endpoints
        ubuntu~$> x_load 200 0.1          # 200 calls, 0.1 s pause in between

    `x_load [calls] [pause]` picks weighted random endpoints (search calls use random terms, so the
    cache misses regularly and Elasticsearch is queried) (so successful calls as well as `4xx` and
    `5xx` responses occur) and prints a status code summary at the end. Every run delivers logs
    (INFO/WARN/ERROR), metrics and traces, including failed ones.

05. Check that all signals arrived in Elasticsearch (metrics are exported every 5-10 seconds, the
    1m aggregations appear after about a minute)

        ubuntu~$> x_otel_status
        .ds-logs-generic.otel-default-...                     184
        .ds-metrics-dockerstatsreceiver.otel-default-...      386
        .ds-metrics-generic.otel-default-...                  915
        .ds-metrics-postgresqlreceiver.otel-default-...       441
        .ds-metrics-redisreceiver.otel-default-...            188
        .ds-metrics-service_destination.1m.otel-default-...    40
        .ds-metrics-service_summary.1m.otel-default-...         4
        .ds-traces-generic.otel-default-...                   381

    * `traces-*`, `logs-*`, `metrics-generic.otel-*` — the app's signals
    * `metrics-postgresqlreceiver.otel-*`, `metrics-redisreceiver.otel-*` — metrics of PostgreSQL and
      Redis (connections, commits, rows, memory, clients, hit/miss rate, ...)
    * `metrics-dockerstatsreceiver.otel-*` — CPU, memory, network and block I/O of every container,
      identified by `container.id`/`container.name`
    * `metrics-service_destination.1m.otel-*` and the other `*.1m.otel-*` — APM aggregations the
      collector derives from the traces (`elasticapm` connector in `otel-collector.yml`); the
      destination metrics feed the dependencies view

06. Log into Kibana (user `elastic`, password `changeme`) and explore the data

        https://localhost:5601

    * **Observability → Applications** — the service `minielk-python-app` with latency, throughput and
      failed transactions; the **Dependencies** tab and the **Service map** show `postgres:5432`, `redis:6379`,
      `es01:9200` (Elasticsearch, only after search requests that missed the cache) and `payment-provider` as downstream dependencies with their latency and error rate
    * The trace waterfall of e.g. `POST /orders` shows the server span and the PostgreSQL/Redis client
      spans below it (the failed `INSERT` carries the exception)
    * **Discover** — data views `logs-*.otel-*`, `metrics-*.otel-*` and `traces-*.otel-*`; logs carry
      the `trace_id`/`span_id` of the call that wrote them
    * Infrastructure side: the service's `container.id`/`host.name` (visible in the service's
      **Infrastructure** tab) match the `container.id` of `metrics-dockerstatsreceiver.otel-*`. The
      `metrics-postgresqlreceiver.otel-*` and `metrics-redisreceiver.otel-*` data streams carry
      `host.name` `postgres`/`redis` — e.g. to chart `app.queue.depth` next to the Redis memory usage

    The infrastructure link shows up about 1-2 minutes after the first calls (it is read from the
    1m aggregations).

07. Shut the stack down (removes the volumes, i.e. also the PostgreSQL data)

        ubuntu~$> x_down

## How it is wired

* **gunicorn:** `app/gunicorn.conf.py` starts 2 worker processes with 4 threads each. The app module
  (and with it the OpenTelemetry SDK with its exporter threads) is imported *inside* each worker, after
  the fork — therefore `preload_app` must stay off. Every worker is its own metric source, so
  `service.instance.id` is set to `<hostname>-<pid>`; without it the workers' identical metric series
  collide in Elasticsearch.
* **Dependencies in Elastic:** `PsycopgInstrumentor` and `RedisInstrumentor` create a client span for
  every statement/command (`db.system`, `db.statement`, ...). The collector's `elasticapm` processor and
  connector turn these into destination metrics, which Kibana renders as dependencies. The
  `transform/destination` processor sets `peer.service` to `<host>:<port>` (`net.peer.*` for psycopg and
  redis, `server.*` for the Elasticsearch client), so the dependencies are called `postgres:5432`,
  `redis:6379` and `es01:9200` (the container hosts) instead of just the `db.system`. `ElasticsearchInstrumentor` traces the Elasticsearch client (`elasticsearch` Python package, the app
  reaches `https://es01:9200` with the CA from the `certs` volume). The external call to `payment-provider` is a manually created client span with the
  attribute `peer.service`.
* **Service ↔ infrastructure:** `app.py` adds `host.name` and — via `opentelemetry-resource-detector-containerid`
  — the 64 character `container.id` to the resource of all signals. Kibana reads them from the traces
  and aggregations and shows them as the service's containers/hosts. The collector's `docker_stats`
  receiver (needs `/var/run/docker.sock`, mounted read-only) delivers the container metrics under the
  same `container.id`.
* **Infrastructure metrics:** the collector's `postgresql` and `redis` receivers query the services
  directly (pipelines `metrics/postgresql` and `metrics/redis`), independent of the app; the
  `resource/*` processors tag them with `host.name` and `service.name`.
* **Limits:** the dependency name (`postgres:5432`) and the `host.name` of the receiver metrics are not
  linked automatically — Kibana has no dependency → container drill-down for OTel data; correlate them
  by `host.name`/`container.name` in Discover or a dashboard.
* The exporters need no code configuration: `docker-compose.yml` sets the standard variables
  `OTEL_EXPORTER_OTLP_ENDPOINT=http://edot-collector:4317`, `OTEL_SERVICE_NAME=minielk-python-app` and
  `OTEL_RESOURCE_ATTRIBUTES=deployment.environment=poc`.
* `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta` is required: Elasticsearch drops histograms
  with cumulative temporality (the collector logs `dropping cumulative temporality histogram`).
* To send your own app's telemetry to this stack, point it at `http://localhost:4317` (gRPC) or
  `http://localhost:4318` (HTTP).
