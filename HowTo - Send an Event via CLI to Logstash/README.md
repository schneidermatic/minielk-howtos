# Sending Events to Logstash/Elasticsearch via CLI (Bash & Python)

Two equivalent scripts generate a random sample event (severity, category, owning team, correlation key,
...) in the [Elastic Common Schema (ECS)](https://www.elastic.co/docs/reference/ecs) and send it either
directly to Elasticsearch's `_doc` API or to a Logstash `http` input:

| Script     | Requirements                                  |
|------------|-----------------------------------------------|
| `event.sh` | Bash, `curl`, `ifconfig` (uses `eth0` IP)      |
| `event.py` | Python >= 3.8, standard library only           |

They are handy for generating test data against any of this repo's stacks that expose Elasticsearch on
`9200` or a Logstash `http` input on `8080` — e.g.
[HowTo - Run a Logstash-to-Logstash Communication](../HowTo%20-%20Run%20a%20Logstash-to-Logstash%20Communication/stack)'s
`ls01`, or [HowTo - Run the ELK Stack with Fleet](../HowTo%20-%20Run%20the%20ELK%20Stack%20with%20Fleet).

## The event (ECS)

```json
{
  "@timestamp": "2026-10-01T16:04:20.671Z",
  "ecs": { "version": "9.0.0" },
  "message": "End2End Monitoring Event",
  "event": { "kind": "alert", "category": ["web"], "type": ["info"], "action": "create-incident",
             "created": "...", "dataset": "insure69.event.common", "module": "End2End",
             "provider": "Insure69_E2E_Monitor", "severity": 3, "reference": "http://www.insure69.de" },
  "host": { "name": "lxv12345", "hostname": "lxv12345", "ip": ["192.168.1.20"] },
  "observer": { "vendor": "SitePerformer", "type": "synthetic" },
  "service": { "name": "Web-Portal" },
  "tags": ["Insure69.com", "Insure69.de"],
  "labels": { "severity_name": "MINOR", "priority": "1", "category": "Performance", "owner": "Team-C",
              "correlation_key": "CK04444", "business_service": "Life Insurance", "page": "Login-Page" }
}
```

`event.severity` is numeric (`0`=UNKNOWN ... `6`=FATAL); values without an ECS equivalent are kept in `labels`.

## Usage

01. Start a stack that exposes Elasticsearch on `9200` and/or a Logstash `http` input on `8080`

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run a Logstash-to-Logstash Communication/stack"
        ubuntu~$> source ./.xrc
        ubuntu~$> x_up

02. Change into this directory (and make the scripts executable on the first run)

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Send an Event via CLI to Logstash"
        ubuntu~$> chmod +x event.sh event.py

### Bash — `event.sh`

03. Usage

        ubuntu~$> ./event.sh -h
          usage: event.sh [-v -h -x option1 -y option2 ...]
                -v verbose
                -d destination, arg(s): 'es' | 'ls'
                -s sleep time (sec.): default 0
                -h help

04. Examples

        # single event straight to Elasticsearch
        ubuntu~$> ./event.sh -d es -v

        # single event to Logstash's http input
        ubuntu~$> ./event.sh -d ls -v

        # continuously, one event every 5 seconds (Ctrl-C to stop)
        ubuntu~$> ./event.sh -d es -s 5

    The target is the host's own `eth0` IP. Credentials, ports and index are variables at the top of
    `event.sh` (`ELASTIC_USER=elastic`, `ELASTIC_PASSWORD=changeme`, `ELASTIC_INDEX=event`).

### Python — `event.py`

05. Usage

        ubuntu~$> ./event.py -h
        usage: event.py [-h] -d {es,ls} [-s SEC] [-v] [--host HOST] [--port PORT]
                        [--index INDEX] [--user USER] [--password PASSWORD]

        options:
          -d {es,ls}, --destination {es,ls}   'es' = Elasticsearch _doc API, 'ls' = Logstash http input
          -s SEC, --sleep SEC                 send continuously, one event every SEC seconds (default: 0 = once)
          -v, --verbose                       print request and payload
          --host HOST                         target host (default: this host's primary IP)
          --port PORT                         target port (default: es=9200, ls=8080)
          --index INDEX                       Elasticsearch index (default: event)
          --user USER                         username (default: elastic)
          --password PASSWORD                 password (default: changeme)

06. Examples (`./event.py` can also be run as `python3 event.py`)

        # single event straight to Elasticsearch
        ubuntu~$> ./event.py -d es -v

        # single event to Logstash's http input on another host/port
        ubuntu~$> ./event.py -d ls --host 192.168.1.10 --port 8081

        # continuously, one event every 5 seconds (Ctrl-C to stop)
        ubuntu~$> ./event.py -d es -s 5

    No dependencies are needed. Optionally, install it as the command `minielk-event` (see
    `pyproject.toml`), ideally into a virtual environment:

        ubuntu~$> python3 -m venv .venv && . .venv/bin/activate
        ubuntu~$> pip install .
        ubuntu~$> minielk-event -d es -s 5

    As with `curl -k` in `event.sh`, the TLS certificate of Elasticsearch is **not** verified (POC stacks use
    a self-signed CA).

## Check the result

    ubuntu~$> curl -k -u elastic:changeme "https://localhost:9200/event*/_search?pretty"
