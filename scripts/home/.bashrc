if [ "X${GOOGLE_APPLICATION_CREDENTIALS}" != "X" ]; then
    gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
    export GCLOUD_PROJECT_ID=$(jq --raw-output '.project_id' ${GOOGLE_APPLICATION_CREDENTIALS})
fi


setenv() {
    export ENV=$1
    source ~/.env/env.${ENV} && export $(cut -d= -f1 < ~/.env/env.${ENV})
}

if [ -f ~/.env/env.dev ]; then
  dev () {
    setenv "dev"
  }
fi

if [ -f ~/.env/env.prod ]; then
  prod () {
    setenv "prod"
  }

  prod
fi