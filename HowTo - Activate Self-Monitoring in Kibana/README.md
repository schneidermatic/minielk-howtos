# Activate Self-Monitoring

This recipe describes how you can activate Elastic's Legacy/Self-Monitoring for the components:

- Elasticsearch
- Logstash
- Kibana

Self-monitoring lets these components ship their own operational metrics (cluster health, node
stats, pipeline stats, ...) straight into the monitoring cluster without running a separate
Metricbeat instance. It reuses whichever MiniELK stack you already have running, as long as it
contains Elasticsearch, Logstash and Kibana — e.g. [HowTo - Run the ELK Stack with Fleet](../HowTo%20-%20Run%20the%20ELK%20Stack%20with%20Fleet).

01. Start a stack that contains Elasticsearch, Logstash and Kibana (e.g. the Fleet stack)

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run the ELK Stack with Fleet"
        ubuntu~$> source ./.xrc
        ubuntu~$> x_up

02. Get your IP-Address with ifconfig

        ubuntu~$> ifconfig

    ![Ubuntu CLI](../resources/images/image01.png)

03. Log into Kibana
        https://<YourIPAddress!!!>:5601

    ![Kibana Login](../resources/images/image02.png)

    **user: elastic**\
    **password: changeme**

04. Turn on self-monitoring

    Since Elastic Stack 9.0, legacy/internal collection is hidden behind a feature flag that is
    off by default — `xpack.monitoring.allow_legacy_collection: true` must be set on each node
    (it's a static setting, so it has to go in `docker-compose.yml`/`elasticsearch.yml` before the
    node starts, not toggled at runtime). This repo's Fleet stack already ships it on `es01` and
    `logstash01`, so you only need to flip the dynamic cluster setting:

    - Open **Stack Management → Data → Monitoring** and click **Turn on monitoring**, which sets
      `xpack.monitoring.collection.enabled: true` on the cluster, or set it directly:

            ubuntu~$> curl -k -u elastic:changeme -X PUT "https://<YourIPAddress>:9200/_cluster/settings" \
                 -H 'Content-Type: application/json' \
                 -d '{"persistent": {"xpack.monitoring.collection.enabled": true}}'

    - Go to **Stack Monitoring** in Kibana to see cluster health, node/index metrics and the
      Logstash pipeline viewer populate.
    - Using a different/your own stack instead? Add both `xpack.monitoring.enabled=true` and
      `xpack.monitoring.allow_legacy_collection=true` (plus the `xpack.monitoring.elasticsearch.*`
      connection settings for Logstash, see this repo's Fleet or Logstash-to-Logstash
      `docker-compose.yml` for examples) to the node(s) you want to self-monitor first.

05. Stop the stack when you're done

        ubuntu~$> x_down
