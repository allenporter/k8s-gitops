#!/bin/bash

cat ~/.kube/kapi01.${ENV}.config | yq '.users[0].user.client-certificate-data' | base64 -d | openssl x509 -in - -noout -enddate
