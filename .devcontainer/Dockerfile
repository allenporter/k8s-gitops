FROM ubuntu:jammy-20250619

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

# Prepare devcontainer workspaces
RUN mkdir /workspaces && chown admin /workspaces

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
        netcat \
        mkisofs \
        age


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

# Cleanup from previous steps
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /src/requirements.txt
RUN pip3 install uv
RUN uv venv
RUN uv pip install -r /src/requirements.txt

# renovate: datasource=github-releases depName=GoogleCloudPlatform/cloud-sdk-docker
ARG GCLOUD_CLI_VERSION=427.0.0
RUN mkdir -p /usr/local/lib/ && \
    cd /usr/local/lib/ && \
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz && \
    tar xf google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-x86_64.tar.gz && \
    /usr/local/lib/google-cloud-sdk/install.sh --quiet --usage-reporting=false --rc-path=/etc/profile

COPY --from=docker.io/bitnami/kubectl:1.33.3            /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl
COPY --from=registry.k8s.io/kustomize/kustomize:v5.7.0  /app/kustomize                   /usr/local/bin/kustomize
COPY --from=instrumentisto/restic:0.18.0-r2             /usr/local/bin/restic            /usr/local/bin/restic
COPY --from=docker.io/alpine/helm:3.18.3                /usr/bin/helm                    /usr/local/bin/helm
COPY --from=ghcr.io/fluxcd/flux-cli:v2.6.4              /usr/local/bin/flux              /usr/local/bin/flux
COPY --from=ghcr.io/siderolabs/talosctl:v1.10.5          /talosctl                        /usr/local/bin/talosctl

ARG ARCH=amd64

# renovate: datasource=github-releases depName=budimanjojo/talhelper
ARG TAL_HELPER_VERSION=v3.0.31
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/budimanjojo/talhelper/releases/download/${TAL_HELPER_VERSION}/talhelper_linux_${ARCH}.tar.gz && \
    tar xf talhelper_linux_${ARCH}.tar.gz && \
    chmod +x talhelper
RUN talhelper --version

# renovate: datasource=github-releases depName=stedolan/jq
ARG JQ_VERSION=1.6
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/stedolan/jq/releases/download/jq-${JQ_VERSION}/jq-linux64 && \
    mv jq-linux64 jq && \
    chmod +x jq
RUN jq --version

# renovate: datasource=github-releases depName=derailed/k9s
ARG K9S_VERSION=v0.50.9
RUN mkdir /usr/local/k9s && \
    cd /usr/local/k9s && \
    curl -OL https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_${ARCH}.tar.gz && \
    tar xf k9s_Linux_${ARCH}.tar.gz && \
    chmod +x k9s && \
    mv k9s /usr/local/bin/k9s && \
    rm -fr /usr/local/k9s
RUN k9s version

# renovate: datasource=github-releases depName=getsops/sops
ARG SOPS_VERSION=v3.10.2
RUN cd /usr/local/bin/ && \
    curl -OL https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.${ARCH} && \
    mv sops-${SOPS_VERSION}.linux.${ARCH} sops && \
    chmod +x sops
RUN sops --version

# renovate: datasource=github-releases depName=yannh/kubeconform
ARG KUBECONFORM_VERSION=v0.7.0
RUN mkdir /usr/local/kubeconfirm/ && \
    cd /usr/local/kubeconfirm/ && \
    curl -OL https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-${ARCH}.tar.gz && \
    tar xf kubeconform-linux-${ARCH}.tar.gz && \
    chmod +x kubeconform && \
    mv kubeconform /usr/local/bin/kubeconform && \
    rm -fr /usr/local/kubeconfirm
RUN kubeconform -v

# renovate: datasource=github-releases depName=go-task/task
ARG TASK_VERSION=v3.44.1
RUN mkdir /usr/local/go-task && \
    cd /usr/local/go-task/ && \
    curl -OL https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_linux_${ARCH}.tar.gz && \
    tar xf task_linux_${ARCH}.tar.gz && \
    cp task /usr/local/bin/task && \
    chmod +x /usr/local/bin/task
RUN task --version

USER admin

# Install inventory plugins and other startup items
COPY --chown=admin:admin bootstrap/env/home/ /home/admin/

# Ansible "unsupported locale setting"
ENV LANG="C.UTF-8"

SHELL ["/bin/bash", "-c"]
