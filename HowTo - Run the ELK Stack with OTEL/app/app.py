"""Flask app (served by gunicorn) using PostgreSQL, Redis and Elasticsearch (search) that emits OpenTelemetry logs, metrics
and traces on every call.

The OTLP endpoint is taken from the standard OTEL_EXPORTER_OTLP_ENDPOINT and
OTEL_SERVICE_NAME environment variables (see docker-compose.yml).
"""
import logging
import os
import random
import socket
import time
from contextlib import contextmanager

import psycopg
import redis
from elasticsearch import Elasticsearch, helpers
from flask import Flask, jsonify, request

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.resource.detector.containerid import ContainerResourceDetector
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode

# The resource identifies this app; service.name is read from OTEL_SERVICE_NAME.
# Every gunicorn worker is its own instance: service.instance.id keeps their metric series apart.
# container.id / host.name tie the service to its infrastructure (Kibana: service -> Infrastructure).
resource = Resource.create({
    "service.version": "1.0.0",
    "service.instance.id": f"{socket.gethostname()}-{os.getpid()}",
    "host.name": socket.gethostname(),
}).merge(ContainerResourceDetector().detect())  # container.id (64 chars, as used by Docker)

# --- Traces ---------------------------------------------------------------
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("minielk.otel.app")

# --- Metrics --------------------------------------------------------------
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=5000)],
)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("minielk.otel.app")
request_counter = meter.create_counter("app.requests", unit="1", description="Number of calls")
work_duration = meter.create_histogram("app.work.duration", unit="ms", description="Simulated work duration")
orders_created = meter.create_counter("app.orders.created", unit="1", description="Orders created")
order_value = meter.create_histogram("app.orders.value", unit="EUR", description="Value of created orders")
cache_requests = meter.create_counter("app.cache.requests", unit="1", description="Cache lookups (hit/miss)")
inflight = meter.create_up_down_counter("app.requests.inflight", unit="1", description="Requests in progress")

# --- Logs (standard python logging, bridged to OTLP) ----------------------
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
set_logger_provider(logger_provider)
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))
log = logging.getLogger("minielk.otel.app")

# --- Infrastructure clients: PostgreSQL, Redis and Elasticsearch --------------------------
# The instrumentors create a client span (db.system, server.address, ...) for every query/command.
# This is what makes 'postgres' and 'redis' show up as dependencies of the service in Kibana.
PsycopgInstrumentor().instrument()
RedisInstrumentor().instrument()
ElasticsearchInstrumentor().instrument()

DSN = "host={host} dbname={db} user={user} password={pw}".format(
    host=os.environ.get("POSTGRES_HOST", "postgres"), db=os.environ.get("POSTGRES_DB", "shop"),
    user=os.environ.get("POSTGRES_USER", "app"), pw=os.environ.get("POSTGRES_PASSWORD", "changeme"))
cache = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), decode_responses=True)

# Elasticsearch serves the product search (the same cluster that stores the telemetry -- fine for a POC)
es = Elasticsearch(
    os.environ.get("ELASTICSEARCH_URL", "https://es01:9200"),
    basic_auth=("elastic", os.environ.get("ELASTIC_PASSWORD", "changeme")),
    ca_certs="/certs/ca/ca.crt",
)
PRODUCT_INDEX = "products"
search_index_ready = False

ORDER_QUEUE = "orders:queue"
meter.create_observable_gauge(
    "app.queue.depth", unit="1", description="Orders waiting in the Redis order queue",
    callbacks=[lambda options: [metrics.Observation(cache.llen(ORDER_QUEUE))]],
)


def db(sql, params=None):
    """Run one statement in PostgreSQL and return all rows (or [] for statements without result)."""
    with psycopg.connect(DSN, autocommit=True) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall() if cur.description else []


app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)  # one server span per HTTP request


@contextmanager
def step(name, lo=0.0, hi=0.0, kind=SpanKind.INTERNAL, **attributes):
    """Child span (optionally simulating lo..hi seconds of work), duration recorded as metric."""
    with tracer.start_as_current_span(name, kind=kind, attributes=attributes) as span:
        start = time.monotonic()
        if hi:
            time.sleep(random.uniform(lo, hi))
        try:
            yield span
        finally:
            work_duration.record((time.monotonic() - start) * 1000, {"step": name})


@app.before_request
def count_inflight():
    inflight.add(1)


@app.after_request
def count_request(response):
    inflight.add(-1)
    request_counter.add(1, {
        "endpoint": request.url_rule.rule if request.url_rule else "unmatched",
        "method": request.method,
        "status": response.status_code,
    })
    return response


@app.errorhandler(psycopg.Error)
def database_error(exc):
    log.error("Database error: %s", exc)
    return jsonify(error="database error"), 500


@app.route("/")
def index():
    log.info("Received a call on /")
    with step("load-data", 0.01, 0.2):
        log.info("Data loaded")
    with step("process-data", 0.01, 0.3):
        log.info("Data processed")
    return jsonify(status="ok")


@app.route("/products")
def products():
    rows = db("SELECT id, name, price FROM products ORDER BY id LIMIT 20")
    log.info("Listed %d products", len(rows))
    return jsonify(count=len(rows))


@app.route("/products/<int:product_id>")
def product(product_id):
    rows = db("SELECT id, name, price FROM products WHERE id = %s", (product_id,))
    if not rows:
        log.warning("Product %d not found", product_id)
        return jsonify(error="product not found"), 404
    log.info("Loaded product %d", product_id)
    return jsonify(id=product_id, name=rows[0][1])


def ensure_search_index():
    """Load the products from PostgreSQL into the Elasticsearch index 'products' (once per worker)."""
    global search_index_ready
    if search_index_ready:
        return
    if not es.indices.exists(index=PRODUCT_INDEX):
        rows = db("SELECT id, name, price FROM products")
        helpers.bulk(es, ({"_index": PRODUCT_INDEX, "_id": r[0], "_source": {"name": r[1], "price": float(r[2])}}
                          for r in rows), refresh=True)  # fixed _id: two workers racing is harmless
        log.info("Indexed %d products into Elasticsearch", len(rows))
    search_index_ready = True


@app.route("/search")
def search():
    term = request.args.get("q", "").lower()
    key = f"search:{term}"
    cached = cache.get(key)
    cache_requests.add(1, {"result": "hit" if cached else "miss"})
    if cached:
        log.info("Search for '%s' served from cache", term)
        return jsonify(q=term, cache="hit", count=int(cached))
    ensure_search_index()
    result = es.search(index=PRODUCT_INDEX, query={"match": {"name": term}} if term else {"match_all": {}}, size=10)
    hits = result["hits"]["total"]["value"]
    cache.setex(key, 10, hits)
    log.info("Search for '%s' served from Elasticsearch (%d hits)", term, hits)
    return jsonify(q=term, cache="miss", count=hits)


@app.route("/login")
def login():
    user = request.args.get("user", "anonymous")
    if user.startswith("bad"):
        attempts = cache.incr(f"login:failed:{user}")
        log.warning("Login failed for user '%s' (%d failed attempts)", user, attempts)
        return jsonify(error="unauthorized"), 401
    cache.setex(f"session:{user}", 60, "active")
    log.info("User '%s' logged in", user)
    return jsonify(user=user)


@app.route("/orders", methods=["POST"])
def create_order():
    # ~10% of the orders reference a non-existing product -> real foreign key violation in PostgreSQL
    product_id = 0 if random.random() < 0.1 else random.randint(1, 50)
    with step("validate-order", 0.005, 0.05):
        pass
    rows = db("INSERT INTO orders (product_id, value) "
              "SELECT id, price FROM products WHERE id = %s RETURNING id, value"
              if product_id else
              "INSERT INTO orders (product_id, value) VALUES (%s, 0) RETURNING id, value",
              (product_id,))
    order_id, value = rows[0]
    cache.rpush(ORDER_QUEUE, order_id)
    orders_created.add(1)
    order_value.record(float(value))
    log.info("Order %d created, value %.2f EUR", order_id, value)
    return jsonify(status="created", id=order_id, value=float(value)), 201


@app.route("/checkout", methods=["POST"])
def checkout():
    with step("reserve-stock"):
        cache.decr("stock:total")
    roll = random.random()
    with tracer.start_as_current_span("POST payment-provider", kind=SpanKind.CLIENT,
                                      attributes={"http.request.method": "POST", "peer.service": "payment-provider"}) as span:
        time.sleep(random.uniform(0.1, 0.6) if roll > 0.05 else 2.0)
        if roll < 0.05:
            exc = TimeoutError("payment provider timed out")
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            log.error("Checkout failed: %s", exc)
            return jsonify(error="payment timeout"), 504
        if roll < 0.2:
            span.set_attribute("http.response.status_code", 402)
            log.warning("Payment declined")
            return jsonify(error="payment declined"), 402
        span.set_attribute("http.response.status_code", 200)
    shipped = cache.lpop(ORDER_QUEUE)
    log.info("Checkout completed, shipped order %s", shipped)
    return jsonify(status="paid", shipped=shipped)


@app.route("/slow")
def slow():
    log.warning("Generating a slow report")
    db("SELECT pg_sleep(%s)", (random.uniform(0.8, 2.0),))
    return jsonify(status="ok")


@app.route("/error")
def error():
    with tracer.start_as_current_span("failing-step") as span:
        try:
            raise RuntimeError("simulated failure")
        except RuntimeError as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            log.error("Call on /error failed: %s", exc)
    return jsonify(status="error"), 500
