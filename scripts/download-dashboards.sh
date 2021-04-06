#!/bin/bash
# Download latest versions of grafana dashboards

set -e

TESLAMATE_VERSION=v1.22.0
TESLAMATE_BASE_URL=https://raw.githubusercontent.com/adriankumpf/teslamate/${TESLAMATE_VERSION}/grafana/dashboards/

TESLAMATE_DASHBOARDS=(charge-level charges charging-stats drive-stats drives efficiency locations mileage overview projected-range states trip updates vampire-drain visited internal/charge-details internal/drive-details)
TESLAMATE_DASHBOARD_DIR=home/base/teslamate/dashboards

indent() { sed 's/^/    /'; }

for DASHBOARD in ${TESLAMATE_DASHBOARDS[@]}; do
  URL=${TESLAMATE_BASE_URL}${DASHBOARD}.json
  echo "Fetching ${URL}"

  DASHBOARD_NAME=${DASHBOARD//\//-}
  OUTPUT_FILE="home/base/teslamate/dashboard-${DASHBOARD_NAME}.yaml"
  JSON_DATA=$(curl -s $URL | indent)

  echo $OUTPUT_FILE

  cat <<EOT >$OUTPUT_FILE
# yamllint disable-file
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-${DASHBOARD_NAME}
  namespace: teslamate
  labels:
    grafana_dashboard: 1
data:
  ${DASHBOARD_NAME}.json: |
${JSON_DATA}
EOT



done
