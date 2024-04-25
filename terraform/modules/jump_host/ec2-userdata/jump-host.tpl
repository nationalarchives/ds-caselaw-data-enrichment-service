#!/bin/bash

# Install useful packages
sudo yum update -y

if ! command -v aws &> /dev/null
then
  sudo yum install -y aws-cli
fi

sudo yum install -y \
  jq \
  rsync
