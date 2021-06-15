# Better SNMP explorer the Rittal PDU

## Setup

1. Setup a SNMP exporter with the `snmp.yml` config.

The config was generated with:

```yaml
modules:
  rittal:
    walk:
      - cmcIIIVarName
      - cmcIIIVarType
      - cmcIIIVarDataType
      - cmcIIIVarUnit
      - cmcIIIVarValueInt
```

Rittal MIBs must be downloaded before. OID explorer here: http://oid-info.com/get/1.3.6.1.4.1.2606.

2. Setup Prometheus with the following config:

```yaml
scrape_configs:
  # ...
  - job_name: 'snmp-exporter'
    scrape_interval:  60s
    scrape_timeout:   30s
    static_configs:
    - targets: ['10.10.3.3'] # A SNMP target
    metrics_path: /snmp
    params:
      module: [rittal]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 10.10.2.107:9116  # The SNMP exporter's real hostname:port.
```

3. Build and run the docker with `build.sh` and `run.sh`.

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
