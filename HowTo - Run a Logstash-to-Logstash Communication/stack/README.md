# Run a Logstash-to-Logstash Communication

This recipe shows how two Logstash instances can talk to each other before data lands in
Elasticsearch: `ls02` receives events on its `http` input (port `8081`) and forwards them on to
`ls01` via its `http` output plugin; `ls01` receives them on its own `http` input (port `8080`,
alongside a `beats` input on `5044` and a `heartbeat` input) and indexes everything into
Elasticsearch (`es01`), routed by the `type` field set on each input.

```
client → ls02:8081 (http in) → ls01:8080 (http in) → es01:9200
```

01. Change into the stack directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run a Logstash-to-Logstash Communication/stack"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (cluster name, ports, memory limit, license mode) and list the available
    shorthands

        ubuntu~$> x_ls

03. Start the stack

        ubuntu~$> x_up

    This brings up `es01`, `kb01`, `ls01` and `ls02`. Each Logstash node loads its own
    `resources/<node>/pipelines.yml` and `resources/<node>/pipeline/event.pipeline`.

04. Send a test event into `ls02` and watch it arrive in Elasticsearch via `ls01`

        ubuntu~$> curl -X POST "http://localhost:8081" -H 'Content-Type: application/json' \
             -d '{"message": "hello from ls02"}'
        ubuntu~$> curl -k -u elastic:changeme "https://localhost:9200/logstash-*/_search?pretty"

    You can also use [HowTo - Send an Event via CLI to Logstash](../../HowTo%20-%20Send%20an%20Event%20via%20CLI%20to%20Logstash)'s
    `event.sh -d ls` against `ls01`'s port `8080` directly.

05. Inspect each node's pipeline stats (self-monitoring is already enabled in this compose file)
    via Kibana's **Stack Monitoring** page, or `GET _nodes/stats/...` on `localhost:9600`/`:9601`.

06. Stop and remove the stack (including its volumes)

        ubuntu~$> x_down
