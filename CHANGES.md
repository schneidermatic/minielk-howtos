# CHANGES

9.5.4 (2026-10-01)
---------------------
* Updated - Files were updated for elastic release '9.5.4'.
* Updated - 'HowTo - Run the ELK Stack with Fleet' now pulls the agent image from
  'docker.elastic.co/elastic-agent/elastic-agent' ('docker.elastic.co/beats/elastic-agent' is gone as of 9.0).
* Updated - 'HowTo - Run a PostgreSQL Connector' now pulls the connector image from
  'docker.elastic.co/integrations/elastic-connectors' ('docker.elastic.co/enterprise-search/elastic-connectors'
  is gone as of 9.0).
* Updated - Legacy/self monitoring now also sets 'xpack.monitoring.allow_legacy_collection=true', required
  since 9.0 to actually activate it.
* Added - 'HowTo - Run the ELK Stack with Elastic Agent'.
* Added - 'HowTo - Run the ELK Stack with OTEL': EDOT Collector plus a Python (Flask/gunicorn) shop app using
  PostgreSQL, Redis and Elasticsearch that sends logs, metrics and traces via OTLP. Dependencies
  ('postgres:5432', 'redis:6379', 'es01:9200', 'payment-provider') show up in Kibana's APM service map, the
  service is tied to its container ('container.id'/'host.name'), and the collector scrapes the PostgreSQL,
  Redis and Docker container metrics. 'x_load' generates a random mix of successful and failing calls.
* Updated - 'HowTo - Send an Event via CLI to Logstash': 'event.sh' sends ECS conformant events, added the
  equivalent 'event.py' (stdlib only, with usage) and a 'pyproject.toml'; the README describes both scripts.
* Updated - README lists 'HowTo - Run the ELK Stack with OTEL'.

8.14.0 (2024-06-08)
---------------------
* Updated - Files were updated for elastic release '8.14.0'.

8.13.4 (2024-06-08)
---------------------
* Updated - Files were updated for elastic release '8.13.4'.






