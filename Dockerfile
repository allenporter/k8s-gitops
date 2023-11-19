
FROM ubuntu:jammy-20231004

RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y --fix-missing \
        curl \
        unzip \
        software-properties-common \
        vim \
        bind9-dnsutils \
        python3-pip \
        sshpass \
        netcat


ARG GO_VERSION=1.19
RUN add-apt-repository ppa:longsleep/golang-backports && \
    apt-get update && \
    apt-get install -y \
        golang-${GO_VERSION} \
        git
ENV PATH $PATH:/usr/lib/go-${GO_VERSION}/bin
RUN go version

# Ceph quincy versions upported by base ubuntu image
RUN apt-get install -y ceph-common
RUN ceph --version

# renovate: datasource=github-releases depName=etcd-io/etcd
ARG ETCD_VERSION=v3.5.10
RUN mkdir -p /src && \
    cd /src && \
    curl -OL https://github.com/etcd-io/etcd/archive/refs/tags/${ETCD_VERSION}.zip && \
    unzip ${ETCD_VERSION}.zip && \
    cd /src/etcd-${ETCD_VERSION#v} && \
    ./build.sh && \
    cp bin/etcdctl /usr/local/bin/etcdctl && \
    rm -fr /src
RUN etcdctl version

# renovate: datasource=github-releases depName=kubernetes/kubernetes versioning=kubernetes-api
ARG KUBECTL_VERSION=v1.27.0
RUN cd /usr/local/bin/ && \
    curl -OL https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
    chmod +x kubectl
RUN kubectl version --client=true

# renovate: datasource=github-releases depName=hashicorp/terraform extractVersion=^v(?<version>.+)$
ARG TERRAFORM_VERSION=1.6.4
RUN mkdir -p /src && \
    cd /src && \
    curl -OL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    cp terraform /usr/local/bin/terraform && \
    rm -fr /src
RUN terraform version

# renovate: datasource=github-releases depName=GoogleCloudPlatform/cloud-sdk-docker
ARG GCLOUD_CLI_VERSION=427.0.0
RUN mkdir -p /usr/local/lib/ && \
    cd /usr/local/lib/ && \
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz && \
    tar xf google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz && \
    /usr/local/lib/google-cloud-sdk/install.sh --quiet --usage-reporting=false --rc-path=/etc/profile

# renovate: datasource=github-releases depName=helm/helm
ARG HELM_CLI_VERSION=v3.13.2
RUN mkdir -p /src && \
    cd /src && \
    curl -OL https://get.helm.sh/helm-${HELM_CLI_VERSION}-linux-amd64.tar.gz && \
    tar xf helm-${HELM_CLI_VERSION}-linux-amd64.tar.gz && \
    cp linux-amd64/helm /usr/local/bin/helm && \
    rm -fr /src
RUN helm version

# renovate: datasource=github-releases depName=fluxcd/flux2 extractVersion=^v(?<version>.+)$
ARG FLUX_CLI_VERSION=2.1.2
RUN mkdir -p /src && \
    cd /src && \
    curl -OL https://github.com/fluxcd/flux2/releases/download/v${FLUX_CLI_VERSION}/flux_${FLUX_CLI_VERSION}_linux_amd64.tar.gz && \
    tar xf flux_${FLUX_CLI_VERSION}_linux_amd64.tar.gz && \
    cp flux /usr/local/bin/flux && \
    rm -fr /src
RUN flux version --client

# renovate: datasource=github-releases depName=kubernetes-sigs/kustomize
ARG KUSTOMIZE_VERSION=v5.0.3
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz && \
    tar xf kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz && \
    chmod +x kustomize
RUN kustomize version

# renovate: datasource=github-releases depName=stedolan/jq
ARG JQ_VERSION=1.6
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/stedolan/jq/releases/download/jq-${JQ_VERSION}/jq-linux64 && \
    mv jq-linux64 jq && \
    chmod +x jq
RUN jq --version

# renovate: datasource=github-releases depName=getsops/sops
ARG SOPS_VERSION=v3.8.1
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.amd64 && \
    mv sops-${SOPS_VERSION}.linux.amd64 sops && \
    chmod +x sops
RUN sops --version

# renovate: datasource=github-releases depName=kyverno/kyverno
ARG KYVERNO_VERSION=v1.11.0
RUN mkdir -p /src && \
    cd /src && \
    curl -OL https://github.com/kyverno/kyverno/releases/download/${KYVERNO_VERSION}/kyverno-cli_${KYVERNO_VERSION}_linux_x86_64.tar.gz && \
    tar xf kyverno-cli_${KYVERNO_VERSION}_linux_x86_64.tar.gz && \
    cp kyverno /usr/local/bin/kyverno && \
    chmod +x /usr/local/bin/kyverno && \
    rm -fr /src
RUN kyverno version

# renovate: datasource=github-releases depName=yannh/kubeconform
ARG KUBECONFORM_VERSION=v0.6.4
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz && \
    tar xf kubeconform-linux-amd64.tar.gz && \
    chmod +x kubeconform
RUN kubeconform -v

# Cleanup from previous steps
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /src/requirements.txt
RUN pip3 install -r /src/requirements.txt

# Setup non-root user
ARG USERNAME=admin
ARG GROUPNAME=admin
RUN addgroup --system ${GROUPNAME} && \
    adduser --system ${GROUPNAME} --ingroup ${USERNAME} --home /home/${USERNAME} --shell /bin/bash && \
    chown -R ${USERNAME}:${GROUPNAME} /home/${USERNAME} && \
    apt-get update && \
    apt-get install -y sudo && \
    echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}
 
USER admin

# Install inventory plugins and other startup items
COPY --chown=admin:admin scripts/home/ /home/admin/

# Ansible "unsupported locale setting"
ENV LANG="C.UTF-8"

SHELL ["/bin/bash", "-c"]