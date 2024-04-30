#!/bin/bash

# Install useful packages
sudo yum update -y

sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm

if ! command -v aws &> /dev/null
then
  sudo yum install -y aws-cli
fi

sudo yum install -y \
  jq \
  rsync \
  vim \
  docker

sudo service docker start
