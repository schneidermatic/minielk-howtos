# Run the ELK Stack with APM Server

This recipe runs Elasticsearch, Kibana and a standalone APM Server, plus a small demo Python web
app (`webapp`, FastAPI + NiceGUI, instrumented with the Elastic APM agent) that sends traces,
errors and custom messages to APM Server so you can see them show up in Kibana's **APM** app.

01. Change into the HowTo directory and source the environment

        ubuntu~$> cd "MiniELK-HOWTOs/HowTo - Run the ELK Stack with APM Server"
        ubuntu~$> source ./.xrc

02. Review/adjust `.env` (stack version, ports, memory limits, `ELASTIC_APM_SECRET_TOKEN`)

03. List the available shorthands, then start the stack

        ubuntu~$> x_ls
        ubuntu~$> x_up

    This brings up `es01`, `kibana`, `apm-server` (configured via `apm-server.yml`, secret-token
    protected) and the `webapp` demo app (built from `app/dockerfile`).

04. Open the demo app and trigger some APM events
        http://localhost:8000

    Use its buttons to generate a Python error, a JS error, or a custom message — each is sent to
    APM Server via the `elastic-apm` client in `app/main.py`.

05. Log into Kibana and open **Observability → APM** to see the `my_python_service` service, its
    transactions and the errors you just triggered
        https://localhost:5601

    **user: elastic**\
    **password: changeme**

06. Stop and remove the stack (including its volumes)

        ubuntu~$> x_down
