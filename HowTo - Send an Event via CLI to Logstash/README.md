# Bash Script for Sending Events to Logstash/Elasticsearch

`event.sh` generates a random sample JSON event (severity, category, owning team, correlation key,
...) and sends it either directly to Elasticsearch's `_doc` API or to a Logstash `http` input, using
the host's own `eth0` IP address as the target. It's handy for generating test data against any of
this repo's stacks that expose Elasticsearch on `9200` or a Logstash `http` input on `8080` — e.g.
[HowTo - Run a Logstash-to-Logstash Communication](../HowTo%20-%20Run%20a%20Logstash-to-Logstash%20Communication/stack)'s
`ls01`, or [HowTo - Run the ELK Stack with Fleet](../HowTo%20-%20Run%20the%20ELK%20Stack%20with%20Fleet).

01. Start a stack that exposes Elasticsearch on `9200` and/or a Logstash `http` input on `8080`

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run a Logstash-to-Logstash Communication/stack"
        ubuntu~$> source ./.xrc
        ubuntu~$> x_up

02. Make the script executable (first run only)

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Send an Event via CLI to Logstash"
        ubuntu~$> chmod +x event.sh

03. Usage

        ubuntu~$> ./event.sh -h
          usage: event.sh [-v -h -x option1 -y option2 ...]
                -v verbose
                -d destination, arg(s): 'es' | 'ls'
                -s sleep time (sec.): default 0
                -h help

04. Send a single event straight to Elasticsearch

        ubuntu~$> ./event.sh -d es -v

05. Send a single event to Logstash's `http` input

        ubuntu~$> ./event.sh -d ls -v

06. Continuously send an event every 5 seconds (Ctrl-C to stop)

        ubuntu~$> ./event.sh -d es -s 5

07. Check the result, e.g. in Elasticsearch directly

        ubuntu~$> curl -k -u elastic:changeme "https://localhost:9200/event*/_search?pretty"

    The script defaults to `ELASTIC_USER=elastic`, `ELASTIC_PASSWORD=changeme` and index `event` —
    edit the variables at the top of `event.sh` if your stack uses different credentials or ports.
