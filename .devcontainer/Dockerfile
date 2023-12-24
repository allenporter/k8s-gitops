
FROM ubuntu:jammy-20231128

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

# renovate: datasource=github-releases depName=hashicorp/terraform extractVersion=^v(?<version>.+)$
ARG TERRAFORM_VERSION=1.6.6
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

COPY --from=docker.io/bitnami/kubectl:1.29.0            /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl
COPY --from=registry.k8s.io/kustomize/kustomize:v5.3.0  /app/kustomize                   /usr/local/bin/kustomize
COPY --from=ghcr.io/kyverno/kyverno-cli:v1.11.1         /ko-app/kubectl-kyverno          /usr/local/bin/kyverno
COPY --from=docker.io/alpine/helm:3.13.3                /usr/bin/helm                    /usr/local/bin/helm
COPY --from=ghcr.io/fluxcd/flux-cli:v2.2.2              /usr/local/bin/flux              /usr/local/bin/flux

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