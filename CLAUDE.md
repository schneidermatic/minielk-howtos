# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of self-contained HowTo recipes ("MiniELK") for standing up small Elastic Stack
(Elasticsearch/Kibana/Logstash/Beats/Fleet/APM) environments with Docker Compose for learning and
proof-of-concept purposes. Each top-level `HowTo - <Title>/` directory is an independent recipe; there
is no shared application code, build system, or test suite — this is infrastructure-as-documentation.

## Layout conventions

- Each `HowTo - <Title>/` directory is self-contained and holds its own `docker-compose.yml`, `.env`,
  and service config files (`kibana.yml`, `logstash.conf`, `filebeat.yml`, `metricbeat.yml`, etc.).
  Some recipes nest the compose project one level deeper under `stack/` (e.g. `HowTo - Run a 3xNode
  Elasticsearch-Cluster/stack/`, `HowTo - Run a Logstash-to-Logstash Communication/stack/`).
- `resources/scripts/` holds the shared shell tooling used by every recipe (`.xrc`, `prereq.sh`,
  `setup.sh`, `newrel.sh`). `resources/images/` holds screenshots embedded in the READMEs.
- `CHANGES.md` at the repo root is a changelog keyed by Elastic Stack release version (e.g. `8.14.0`),
  not by commit.
- Commit messages follow the pattern `* <Added|Updated|Removed> - '<HowTo or file name>' <description>.`
  (see `git log`).

## The `.xrc` command convention

Every recipe directory ships a `.xrc` file: a shell snippet sourced into the current shell that sets
`PROJECT_HOME` (the recipe dir) and `RESOURCES_HOME` (path to the shared `resources/` dir, relative
depth depends on nesting), then sources `$RESOURCES_HOME/scripts/.xrc` for the common `x_*` functions:

- `x_up` — `docker-compose up -d` then prints connection details (`x_show_details`)
- `x_down` — `docker-compose down -v`
- `x_setup` — runs the shared host prerequisite script (`prereq.sh`: sysctl/ulimit tuning for ES)
- `x_newrel` — interactively bumps `STACK_VERSION` across `.env` files
- `x_ls` — lists all available `x_*` commands in the current shell
- `x_banner` / `x_show_details` — prints the MiniELK banner and default Kibana URL/credentials

Individual recipes add their own `x_*` functions on top (e.g. `x_getcert` in the Fleet HowTo, which
pulls the CA cert out of the running ES container and prints its SHA-256 fingerprint for Fleet
enrollment).

To work in a given recipe: `cd "HowTo - <Title>"` (or its `stack/` subdir), `. .xrc`, then use the
`x_*` commands. There is no separate build/lint/test tooling — "testing" a change means running
`x_up`, verifying the stack comes up healthy and Kibana/Fleet/APM behaves as the README describes,
then `x_down`.

## `.env` conventions

- `STACK_VERSION` pins the Elastic product version for the whole recipe; keep every service image tag
  on this variable rather than hardcoding versions.
- `ELASTIC_PASSWORD` / `KIBANA_PASSWORD` / `ENCRYPTION_KEY` are POC-only sample secrets (`changeme`,
  a static encryption key) — expected and fine for this repo's purpose, not a vulnerability to flag.
- `*_MEM_LIMIT` variables tune container memory; adjust relative to host resources, not stack logic.

## Docker Compose conventions

- A `setup` service typically runs first (via `depends_on: condition: service_healthy`) to generate
  the CA and per-node TLS certs with `elasticsearch-certutil` into a shared `certs` volume before
  `es01` and friends start.
- Healthchecks gate startup ordering (e.g. Kibana waits on `es01`'s healthcheck, Beats/Logstash wait
  on Kibana's). When adding a new service, follow this `depends_on` + `healthcheck` chain pattern
  rather than fixed sleeps.
- Default network is named `elastic` (or declared explicitly per-recipe) so services across a
  recipe's containers can resolve each other by service name.

## Writing READMEs

Recipe READMEs are numbered step-by-step walkthroughs (`01.`, `02.`, ...) mixing shell snippets and
embedded screenshots from `../resources/images/`. Several existing READMEs are intentionally
incomplete (`TODO`/`ToDo` placeholders) — this is expected, not a sign of broken content.
