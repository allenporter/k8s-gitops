FROM alpine:3.7
ENV KUBEVAL_VERSION=0.15.0 \
    KUSTOMIZE_VERSION=4.0.1

RUN apk add --no-cache curl

RUN curl -sLf https://github.com/instrumenta/kubeval/releases/download/${KUBEVAL_VERSION}/kubeval-linux-amd64.tar.gz \
    && tar xf kubeval-linux-amd64.tar.gz \
    && mv kubeval /usr/local/bin \
    && rm -rf kubeval-linux-amd64.tar.gz

RUN curl -sLf https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz -o kustomize.tar.gz\
    && tar xf kustomize.tar.gz \
    && mv kustomize /usr/local/bin \
    && chmod +x /usr/local/bin/kustomize \
    && rm -rf kustomize.tar.gz

CMD ["kustomize"]
