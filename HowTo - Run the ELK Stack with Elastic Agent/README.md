# Run the ELK Stack with Elastic Agent

This recipe runs Elasticsearch, Kibana, a Fleet Server, and a Fleet-managed **Elastic Agent**
running the `system` integration (host logs/metrics). Kibana is pre-configured
(`kibana.yml`) with two agent policies — `Fleet-Server-Policy` for the Fleet Server itself and
`Elastic-Agent-Policy` (with the `system` integration enabled) for the actual Elastic Agent — and
both the Fleet Server and the Elastic Agent enroll themselves automatically on `x_up`, fetching
their enrollment token from Kibana by policy name (`FLEET_TOKEN_POLICY_NAME`). There is no manual
enrollment step: no copying a token from Kibana's **Add agent** flyout, no pasting an `elastic-agent
enroll` command anywhere.

01. Change into the HowTo directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run the ELK Stack with Elastic Agent"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (stack version, ports, memory limits)

03. List the available shorthands, then start the stack

        ubuntu~$> x_ls
        ubuntu~$> x_up

    This brings up `es01` and `kibana`, then `fleet-server` (which bootstraps Fleet in Kibana and
    enrolls itself into `Fleet-Server-Policy`), then `elastic-agent` (which waits for the Fleet
    Server's `/api/status` to report `HEALTHY` and enrolls itself into `Elastic-Agent-Policy`).

04. Log into Kibana
        https://localhost:5601

    **user: elastic**\
    **password: changeme**

05. Open **Management → Fleet → Agents** — the Elastic Agent already shows up there as
    **Healthy**, enrolled under `Elastic-Agent-Policy`, with no action needed from you. Open
    **Management → Fleet → Agent policies → Elastic-Agent-Policy** to see the `system` integration
    it's running.

06. Open **Discover** or **Dashboards** (search for "System") to see host logs/metrics flowing in
    from the agent — the container's own `/proc`, `/sys` and Docker socket are bind-mounted in, so
    the System integration reports on the Docker host rather than on an empty container.

07. Check enrollment/agent status directly from the CLI if you want to confirm it without Kibana

        ubuntu~$> x_agent_status

08. Stop and remove the stack (including its volumes)

        ubuntu~$> x_down

    Since enrollment state lives in the `fleetserverdata`/`elasticagentdata` volumes, `x_down`
    wipes it; the next `x_up` re-enrolls both agents from scratch against the fresh Elasticsearch
    data, exactly as described above.
