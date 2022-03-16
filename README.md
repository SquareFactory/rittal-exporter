# Better SNMP explorer the Rittal PDU

## Setup

1. Setup Prometheus with the following config:

```yaml
scrape_configs:
  - job_name: 'better-snmp-exporter'
    static_configs:
      - targets: ['better-snmp-exporter:8123']
    metrics_path: /
```

2. Build and run the docker with `build.sh` and `run.sh`.

## Configuration

Environment variables:

```sh
ENV PORT 8123
ENV PROMETHEUS_URL http://10.10.2.107:9090
ENV UPDATE_PERIOD_S 60
```

Config YAML to label PDU port:

```json
{
  "bindings": [
    {
      "socket": 1,
      "node": "cn1"
    },
    // ...
    {
      "socket": 28,
      "node": "cn12"
    }
  ]
}
```
