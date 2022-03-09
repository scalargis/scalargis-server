FROM ubuntu:20.04

MAINTAINER ricardo.sena@wkt.pt

RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
  iputils-ping \
  nodejs npm \
  python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Add app components
ADD . /var/scalargis

# Set working dir
WORKDIR /var/scalargis

# Install ScalarGIS dependencies
RUN pip3 install -r requirements.txt --cache-dir .pip-cache && rm -rf .pip-cache

RUN LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "npm install -g gulp bower && npm install && bower install --allow-root && gulp"

# Expose default port
EXPOSE 5000

# Set source folder
WORKDIR /var/scalargis/web
