# Run a PostgreSQL Connector

This recipe runs Elasticsearch, Kibana, a PostgreSQL database, pgAdmin, and a self-managed
[Elastic connector](https://www.elastic.co/docs/reference/search-connectors/es-postgresql-connector-client-tutorial)
(`ec01`, image `docker.elastic.co/integrations/elastic-connectors`) that syncs data from
PostgreSQL into Elasticsearch indices. The connector service version must match the
Elasticsearch version it talks to, so `ec01` is pinned to the same `${STACK_VERSION}` as
Elasticsearch and Kibana.

A `connector-setup` container does the connector setup automatically as part of `x_up` — it
creates the `postgresql-connector` connector via the
[Connector API](https://www.elastic.co/docs/reference/search-connectors/api-tutorial), fills in
its PostgreSQL connection details from `.env`, writes `connector-config/config.yml` for `ec01`,
and kicks off an initial full sync. Nothing needs to be configured by hand in Kibana.

01. Change into the HowTo directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run a PostgreSQL Connector"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (stack version, cluster name, ports, memory limit, license mode, and the
    PostgreSQL/pgAdmin credentials below — `docker-compose.yml` picks them all up directly)

        POSTGRES_DEFAULT_IMAGE=postgres:17-alpine
        POSTGRES_USER=pgadmin
        POSTGRES_PASSWORD=changeme
        POSTGRES_DB=elasticdb
        POSTGRES_PORT=5432
        PGADMIN_EMAIL=admin@servfolio.com
        PGADMIN_PASSWORD=admin123
        PGADMIN_PORT=5050

03. List the available shorthands, then start the stack

        ubuntu~$> x_ls
        ubuntu~$> x_up

    `x_up` brings up Elasticsearch, Kibana, PostgreSQL and pgAdmin, then `connector-setup` runs
    once (it waits on Elasticsearch and PostgreSQL being healthy) to create the connector, write
    `connector-config/config.yml`, and trigger an initial full sync — only once that has finished
    does `ec01` start and pick up the generated config.

04. Access pgAdmin to inspect the PostgreSQL data that gets synced
        http://localhost:5050 (or whatever `PGADMIN_PORT` is set to)

    Log in with the `PGADMIN_EMAIL` / `PGADMIN_PASSWORD` from `.env` (defaults:
    `admin@servfolio.com` / `admin123`). pgAdmin itself doesn't come with the `postgres` server
    pre-registered, so add it once via **Object → Register → Server...**:

    - **General** tab → Name: anything, e.g. `MiniELK Postgres`
    - **Connection** tab:
        - Host name/address: `postgres` (the Docker service name — not `localhost`, since pgAdmin
          reaches it over the `elastic` Docker network, not through the published host port)
        - Port: `5432`
        - Maintenance database: `${POSTGRES_DB}` (default `elasticdb`)
        - Username: `${POSTGRES_USER}` (default `pgadmin`)
        - Password: `${POSTGRES_PASSWORD}` (default `changeme`)

    Once registered, you can browse `elasticdb`'s schemas/tables under **Servers → MiniELK
    Postgres → Databases → elasticdb** — the same data the `postgresql-connector` connector syncs
    into Elasticsearch.

05. In Kibana (**Search → Content → Connectors**), open the **PostgreSQL Connector** to watch the
    sync progress and confirm documents land in the `search-postgresql` index — no setup step is
    needed there, it's for observing the already-running sync.

06. Stop and remove the stack (including its volumes)

        ubuntu~$> x_down

    Since `connector-setup` only runs once per `docker-compose` project lifetime, a subsequent
    `x_up` after `x_down` recreates the connector from scratch (matching the fresh Elasticsearch
    data); on a plain restart (`docker compose restart` / `docker compose up -d` without `x_down`
    first) it's skipped, since `connector-config/config.yml` and the connector already exist.
