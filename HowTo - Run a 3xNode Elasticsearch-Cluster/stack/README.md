# Run a 3xNode Elasticsearch-Cluster

This recipe starts a 3-node Elasticsearch cluster (`es01`, `es02`, `es03`) plus a single Kibana
(`kb01`), all secured with TLS certificates generated on first start. It's useful for exploring
cluster formation, shard allocation and node failure behaviour without needing three separate hosts.

01. Change into the stack directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run a 3xNode Elasticsearch-Cluster/stack"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (cluster name, ports, memory limit, license mode) and list the available
    shorthands

        ubuntu~$> x_ls

03. Start the cluster

        ubuntu~$> x_up

    The `setup` service generates a CA and per-node certificates (`es01`, `es02`, `es03`, `kb01`)
    into a shared `certs` volume before any node starts; each Elasticsearch node then waits on the
    previous one via `depends_on`/`healthcheck`.

04. Verify the cluster is green and has 3 nodes

        ubuntu~$> curl -k -u elastic:changeme https://localhost:9200/_cluster/health?pretty

05. Log into Kibana
        https://localhost:5601

    **user: elastic**\
    **password: changeme**

06. Stop and remove the cluster (including its volumes)

        ubuntu~$> x_down
