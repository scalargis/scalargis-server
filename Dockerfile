FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0

LABEL maintainer="ricardo.sena@wkt.pt"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  iputils-ping \
  python3-pip \
  libfontconfig1-dev \
  && rm -rf /var/lib/apt/lists/*

ADD . /var/scalargis

WORKDIR /var/scalargis

RUN pip3 install --break-system-packages -r requirements.txt --cache-dir .pip-cache && rm -rf .pip-cache

WORKDIR /var/scalargis/scalargis
