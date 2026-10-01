# Run the ELK Stack with Fleet

This recipe runs a fuller ELK Stack managed partly through Fleet: Elasticsearch, Kibana,
Fleet Server (which doubles as the APM integration endpoint), Metricbeat, Filebeat, Logstash, and
a small instrumented demo web app (`webapp`). Kibana is pre-configured (`kibana.yml`) to install
the `fleet_server`, `system`, `elastic_agent` and `apm` packages and to create a
`Fleet-Server-Policy` automatically.

01. Change into the HowTo directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run the ELK Stack with Fleet"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (stack version, ports, memory limits, `ELASTIC_APM_SECRET_TOKEN`)

03. List the available shorthands, then start the stack

        ubuntu~$> x_ls
        ubuntu~$> x_up

    This brings up `es01`, `kibana`, `metricbeat01`, `filebeat01`, `logstash01`, `fleet-server`
    and the `webapp` demo app. Filebeat tails `./filebeat_ingest_data`, Logstash tails
    `./logstash_ingest_data` (both pre-loaded with a sample `Air_Quality` dataset).

04. Log into Kibana
        https://localhost:5601

    **user: elastic**\
    **password: changeme**

05. Get the Fleet CA fingerprint (needed to enroll additional Elastic Agents)

        ubuntu~$> x_getcert

    This pulls `ca.crt` out of the running Elasticsearch container into `./cert`, prints its
    SHA-256 fingerprint and the certificate itself.

06. Open **Management → Fleet** in Kibana to see the `fleet-server` agent enrolled under
    `Fleet-Server-Policy`, and enroll further agents using the printed fingerprint if needed.

07. Open the demo app and trigger some APM events, then check **Observability → APM** in Kibana
        http://localhost:8000

08. Stop and remove the stack (including its volumes)

        ubuntu~$> x_down
