#!/bin/sh

docker run -d --rm \
           --name better-snmp-exporter \
           -v "$(pwd)/config.json":/app/config.json \
           -p 8123:8123 \
           better-snmp-exporter
