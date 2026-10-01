# MiniELK-HOWTOs

<img src="resources/images/MiniELK-Logo01.png" width="250">

This repository contains a collection of MiniELK-HOWTOs for learning/demo purposes. Each HowTo is a
self-contained Docker Compose recipe that spins up a small Elastic Stack (Elasticsearch, Kibana,
Logstash, Beats, Fleet, APM Server, ...) environment.

## TABLE OF CONTENTS
<ol>
<li><a href="#tested-with">Tested With</a></li>
<li><a href="#content">Content</a></li>
<li><a href="#setup">Setup</a></li>
<li><a href="#run">Run</a></li>
<li><a href="#stop">Stop</a></li>
<li><a href="#contributing">Contributing</a></li>
</ol>

## TESTED WITH
The HowTos are tested with the following software components...

Name            | Reference
--------------- | ---------------
Windows         | >= 11
Docker Desktop  | >= 4.12.0
WSL             | >= 2
Ubuntu          | >= 20.04.6 LTS (Focal Fossa)
docker          | >= 20.10.17
docker-compose  | >= v2.10.2
Elastic Stack   | pinned per HowTo via `STACK_VERSION` in its `.env` file

## CONTENT
Id  | Description
----|----------------------------------------------------------------------
001 | [HowTo - Activate Self-Monitoring in Kibana](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Activate%20Self-Monitoring%20in%20Kibana)
002 | [HowTo - Run a 3xNode Elasticsearch-Cluster](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20a%203xNode%20Elasticsearch-Cluster/stack)
003 | [HowTo - Run a Logstash-to-Logstash Communication](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20a%20Logstash-to-Logstash%20Communication/stack)
004 | [HowTo - Run a PostgreSQL Connector](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20a%20PostgreSQL%20Connector)
005 | [HowTo - Run the ELK Stack with APM Server](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20the%20ELK%20Stack%20with%20APM%20Server)
006 | [HowTo - Run the ELK Stack with Elastic Agent](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20the%20ELK%20Stack%20with%20Elastic%20Agent)
007 | [HowTo - Run the ELK Stack with Fleet](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20the%20ELK%20Stack%20with%20Fleet)
008 | [HowTo - Send an Event via CLI to Logstash](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Send%20an%20Event%20via%20CLI%20to%20Logstash)
009 | [HowTo - Run the ELK Stack with OTEL](https://github.com/schneidermatic/MiniELK-HOWTOs/tree/main/HowTo%20-%20Run%20the%20ELK%20Stack%20with%20OTEL)

## SETUP
1. Clone the MiniELK-HOWTOs repo

        $ cd ~
        $ git clone git@github.com:schneidermatic/MiniELK-HOWTOs.git

2. Select one of the HowTos i.e.

        $ cd MiniELK-HOWTOs/"HowTo - Run the ELK Stack with Fleet"
        $ source ./.xrc

3. Copy the HowTo's `.env` file and adjust it to your needs (stack version, ports, passwords, memory limits)

## RUN
1. Source the HowTo environment (again)

        $ cd MiniELK-HOWTOs/"HowTo - Run the ELK Stack with Fleet"
        $ source ./.xrc

2. List all shorthands

        $ x_ls

3. Start the stack

        $ x_up

4. Open your browser and go to https://localhost:5601 (default Kibana port, see the HowTo's `.env`)

   **user: elastic**\
   **password: changeme**

## STOP
1. Stop and remove the stack (including its volumes)

        $ x_down

## CONTRIBUTING
Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
