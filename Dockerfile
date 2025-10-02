FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0

MAINTAINER ricardo.sena@wkt.pt

RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
  iputils-ping \
  python3-pip \
  libfontconfig1-dev \
  && rm -rf /var/lib/apt/lists/*

# Add app components
ADD . /var/scalargis

# Set working dir
WORKDIR /var/scalargis

# Install python dependencies
RUN apt install libcairo2-dev pkg-config python3-dev

# Install ScalarGIS dependencies
RUN pip3 install --break-system-packages -r requirements.txt --cache-dir .pip-cache && rm -rf .pip-cache

# Set source folder
WORKDIR /var/scalargis/scalargis
