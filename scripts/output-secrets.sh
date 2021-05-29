#!/bin/bash
#
# Retrieve all secrets from the cluster and output as environment variables. The output can be saved in
# the .env file so they persisted and can be re-recreated in the future.

set -e

CONTEXT_ARG=$1
CONTEXT=${CONTEXT_ARG:-$ENV}
if [[ ! "$CONTEXT" =~ ^(dev|prod|template)$ ]]; then
  echo "Usage: $0 <dev|prod|template>"
  exit 1
fi

KUBECTL_FLAGS="--context=${CONTEXT}-context --ignore-not-found=true"

function get_secret() {
  if [ "${CONTEXT}" == "template" ]; then
    echo ""
    return 0
  fi
  secret_name=$1
  namespace=$2
  key=$3
  kubectl get secret ${secret_name} -n ${namespace} ${KUBECTL_FLAGS} -o jsonpath="{.data.${key}}" | base64 --decode
  return 0
}


# Ensure in git repo
git -C . rev-parse 2>/dev/null

if [ ! -d ".git" ]; then
  echo "Must be run from git root path"
  exit 1
fi

SECRETS_DIR="scripts/.secrets"
if [ ! -d ${SECRETS_DIR} ]; then
  mkdir ${SECRETS_DIR}
fi

# kubectl get secret generic postgresql-password -n home-assistant --from-literal="data=${HA_POSTGRESQL_PWD}"
echo export HA_POSTGRESQL_PWD=$(get_secret "postgresql-password" "home-assistant" "data")

# kubectl create secret generic discord-alert -n monitoring --from-literal=address="${PROMETHEUS_DISCORD_ALERT_URL}"
echo export PROMETHEUS_DISCORD_ALERT_URL=$(get_secret "discord-alert" "monitoring" "address")

# kubectl create secret generic discord-url -n flux-system --from-literal="address=${FLUX_DISCORD_URL}"
echo export FLUX_DISCORD_URL=$(get_secret "discord-url" "flux-system" "address")

# kubectl create secret generic discord-alert-url -n flux-system --from-literal="address=${FLUX_DISCORD_ALERT_URL}"
echo export FLUX_DISCORD_ALERT_URL=$(get_secret "discord-alert-url" "flux-system" "address")

# kubectl create secret generic external-dns-key -n external-dns --from-literal="rfc2136_tsig_secret=${EXTERNAL_DNS_KEY}"
echo export EXTERNAL_DNS_KEY=$(get_secret "external-dns-key" "external-dns" "rfc2136_tsig_secret")

# kubectl create secret generic grafana -n monitoring --from-literal="admin-password=${GRAFANA_ADMIN_PASSWORD}" --from-literal="admin-user=${GRAFANA_ADMIN_USER}"
echo export GRAFANA_ADMIN_USER=$(get_secret "grafana" "monitoring" "admin-user")
echo export GRAFANA_ADMIN_PASSWORD=$(get_secret "grafana" "monitoring" "admin-password")

# kubectl create secret generic prometheus-bearer-token -n home-assistant --from-literal="token=${PROMETHEUS_HA_BEARER_TOKEN}"
echo export PROMETHEUS_HA_BEARER_TOKEN=$(get_secret "prometheus-bearer-token" "home-assistant" "token")

# kubectl create secret generic pihole-password -n pihole --from-literal="password=${PIHOLE_ADMIN_PASSWORD}"
echo export PIHOLE_ADMIN_PASSWORD=$(get_secret "pihole-password" "pihole" "password")

# kubectl create secret generic minecraft-rcon-password -n minecraft --from-literal="password=${RCON_PASSWORD}"
echo export RCON_PASSWORD=$(get_secret "minecraft-rcon-password" "minecraft" "password")

CLOUD_DNS_KEY_FILE="${SECRETS_DIR}/clouddns-dns01-key.json"
if [ "${CONTEXT}" == "template" ]; then
  CLOUD_DNS_KEY_FILE=""
elif [ ! -f ${CLOUD_DNS_KEY_FILE} ]; then
  CLOUD_DNS_KEY_JSON=$(get_secret "clouddns-dns01-solver-svc-acct" "cert-manager" "key\.json")
  echo ${CLOUD_DNS_KEY_JSON} > ${CLOUD_DNS_KEY_FILE}
fi
echo export CLOUD_DNS_KEY_FILE=${CLOUD_DNS_KEY_FILE}
