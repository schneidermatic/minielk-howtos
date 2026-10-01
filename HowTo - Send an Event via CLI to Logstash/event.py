#!/usr/bin/env python3
# ******************************************************************************
# Copyright 2019 the original author or authors.                              *
#                                                                             *
# Licensed under the Apache License, Version 2.0 (the "License");             *
# you may not use this file except in compliance with the License.            *
# You may obtain a copy of the License at                                     *
#                                                                             *
# http://www.apache.org/licenses/LICENSE-2.0                                  *
#                                                                             *
# Unless required by applicable law or agreed to in writing, software         *
# distributed under the License is distributed on an "AS IS" BASIS,           *
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    *
# See the License for the specific language governing permissions and         *
# limitations under the License.                                              *
# ******************************************************************************
#
# SCRIPT:  event.py
# PURPOSE: Python equivalent of event.sh - sends a random ECS conformant
#          custom event to Elasticsearch or a Logstash http input.
#          Uses the Python standard library only.

import argparse
import base64
import json
import random
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ELASTIC_USER = "elastic"
ELASTIC_PASSWORD = "changeme"
ELASTIC_INDEX = "event"
ELASTICSEARCH_PORT = 9200
LOGSTASH_PORT = 8080

SEVERITIES = ["UNKNOWN", "HARMLESS", "WARNING", "MINOR", "MAJOR", "CRITICAL", "FATAL"]
PAGES = ["Landing-Page", "Login-Page", "Product-Page", "Order-Page", "Account-Page"]
CATEGORIES = ["Availability", "Accuracy", "Performance"]
TEAMS = ["Team-A", "Team-B", "Team-C"]
CORRELATION_KEYS = ["CK01111", "CK02222", "CK03333", "CK04444", "CK05555"]
BUSINESS_SERVICES = [
    "Travel Insurance",
    "Health Insurance",
    "Life Insurance",
    "Car Insurance",
    "Home Insurance",
]


def create_message():
    """Build a random event following the Elastic Common Schema (ECS).

    event.severity is numeric (0=UNKNOWN .. 6=FATAL); fields without an ECS
    equivalent go to 'labels' (flat keyword key/values).
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    severity_idx = random.randrange(len(SEVERITIES))
    hostname = "lxv12345"

    return {
        "@timestamp": timestamp,
        "ecs": {"version": "9.0.0"},
        "message": "End2End Monitoring Event",
        "event": {
            "kind": "alert",
            "category": ["web"],
            "type": ["info"],
            "action": "create-incident",
            "created": timestamp,
            "dataset": "insure69.event.common",
            "module": "End2End",
            "provider": "Insure69_E2E_Monitor",
            "severity": severity_idx,
            "reference": "http://www.insure69.de",
        },
        "host": {
            "name": hostname,
            "hostname": hostname,
            "ip": [f"192.168.1.{random.randrange(100)}"],
        },
        "observer": {"vendor": "SitePerformer", "type": "synthetic"},
        "service": {"name": "Web-Portal"},
        "tags": ["Insure69.com", "Insure69.de"],
        "labels": {
            "severity_name": SEVERITIES[severity_idx],
            "priority": str(random.randrange(5)),
            "category": random.choice(CATEGORIES),
            "owner": random.choice(TEAMS),
            "correlation_key": random.choice(CORRELATION_KEYS),
            "business_service": random.choice(BUSINESS_SERVICES),
            "page": random.choice(PAGES),
        },
    }


def local_ip():
    """Primary outbound IPv4 address of this host (no packets are sent)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def send_event(args):
    host = args.host or local_ip()
    body = json.dumps(create_message()).encode()
    auth = base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
    headers = {"Content-Type": "application/json", "Authorization": f"Basic {auth}"}

    if args.destination == "es":
        url = f"https://{host}:{args.port or ELASTICSEARCH_PORT}/{args.index}/_doc"
        target = "elasticsearch"
        ctx = ssl.create_default_context()  # equivalent of curl -k
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:
        url = f"http://{host}:{args.port or LOGSTASH_PORT}"
        target = "logstash"
        ctx = None

    if args.verbose:
        print(f"POST {url}\n{body.decode()}")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10):
            pass
        print(f"SUCCESS - Event was send to {target}.")
    except (urllib.error.URLError, OSError) as exc:
        print(f"ERROR - Event couldn't be send to {target}: {exc}")


def parse_args():
    parser = argparse.ArgumentParser(
        prog="event.py",
        description="Send a random ECS conformant event to Elasticsearch or Logstash.",
    )
    parser.add_argument("-d", "--destination", required=True, choices=["es", "ls"],
                        help="'es' = Elasticsearch _doc API, 'ls' = Logstash http input")
    parser.add_argument("-s", "--sleep", type=float, default=0, metavar="SEC",
                        help="send continuously, one event every SEC seconds (default: 0 = send once)")
    parser.add_argument("-v", "--verbose", action="store_true", help="print request and payload")
    parser.add_argument("--host", help="target host (default: this host's primary IP)")
    parser.add_argument("--port", type=int,
                        help=f"target port (default: es={ELASTICSEARCH_PORT}, ls={LOGSTASH_PORT})")
    parser.add_argument("--index", default=ELASTIC_INDEX, help="Elasticsearch index (default: %(default)s)")
    parser.add_argument("--user", default=ELASTIC_USER, help="username (default: %(default)s)")
    parser.add_argument("--password", default=ELASTIC_PASSWORD, help="password (default: %(default)s)")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.sleep > 0:
            while True:
                send_event(args)
                time.sleep(args.sleep)
        else:
            send_event(args)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
