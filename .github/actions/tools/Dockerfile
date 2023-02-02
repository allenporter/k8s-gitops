FROM alpine:3.17

ENV KUSTOMIZE_VERSION=4.1.2
ENV KYVERNO_VERSION=v1.7.2

RUN apk add --no-cache curl

RUN curl -sLf https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz -o kustomize.tar.gz \
    && tar xf kustomize.tar.gz \
    && mv kustomize /usr/local/bin \
    && chmod +x /usr/local/bin/kustomize \
    && rm -rf kustomize.tar.gz

RUN curl -sLf https://github.com/kyverno/kyverno/releases/download/${KYVERNO_VERSION}/kyverno-cli_${KYVERNO_VERSION}_linux_x86_64.tar.gz -o kyverno-cli.tar.gz \
    && tar xf kyverno-cli.tar.gz \
    && mv kyverno /usr/local/bin \
    && chmod +x /usr/local/bin/kyverno \
    && rm -fr kyverno-cli.tar.gz

CMD ["kustomize", "version"]
