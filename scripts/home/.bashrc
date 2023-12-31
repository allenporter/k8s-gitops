if [ "X${GOOGLE_APPLICATION_CREDENTIALS}" != "X" ]; then
    gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
    export GCLOUD_PROJECT_ID=$(jq --raw-output '.project_id' ${GOOGLE_APPLICATION_CREDENTIALS})
fi

# No default cluster config or ansible inventory at the moment
# KUBECONFIG="${HOME}/.env/kapi01.config"
# ANSIBLE_INVENTORY="${ENV_INVENTORY_ROOT}/prod/inventory.yaml"
