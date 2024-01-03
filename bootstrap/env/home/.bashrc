if [ "X${GOOGLE_APPLICATION_CREDENTIALS}" != "X" ]; then
    gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
    export GCLOUD_PROJECT_ID=$(jq --raw-output '.project_id' ${GOOGLE_APPLICATION_CREDENTIALS})
fi

export KUBECONFIG="${HOME}/.env/kubeconfig.yaml"

# No default ansible inventory at the moment
# ANSIBLE_INVENTORY="${ENV_INVENTORY_ROOT}/prod/inventory.yaml"
