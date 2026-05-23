# ---------------------------------------------------------------------------
# Stage 1 — Build the frontend (viewer + backoffice)
# ---------------------------------------------------------------------------
FROM node:24 AS build

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

WORKDIR /var/scalargis

ADD ./scalargis-client /var/scalargis

RUN test -z "$HTTP_PROXY" || npm config set proxy $HTTP_PROXY && :
RUN test -z "$HTTPS_PROXY" || npm config set https-proxy $HTTPS_PROXY && :

RUN npm install

# Copy deployment env files if provided
# COPY ./configs/.env.backoffice apps/backoffice/.env
# COPY ./configs/.env.viewer apps/viewer/.env

# Copy project-specific components and themes if needed
# COPY ./scalargis-components/ apps/backoffice/src/app/components/
# COPY ./scalargis-components/ apps/viewer/src/app/components/
# COPY ./scalargis-themes/ apps/viewer/src/app/themes/

RUN npx nx run-many -t build --verbose

# ---------------------------------------------------------------------------
# Stage 2 — Deploy server + built client
# ---------------------------------------------------------------------------
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

# Copy built frontend from build stage
COPY --from=build /var/scalargis/dist/apps/viewer /var/scalargis/scalargis/app/static/viewer
COPY --from=build /var/scalargis/dist/apps/backoffice /var/scalargis/scalargis/app/static/backoffice

# Install extra Python requirements for extensions if needed
# COPY requirements-extra.txt .
# RUN pip3 install -r requirements-extra.txt --break-system-packages --cache-dir .pip-cache && rm -rf .pip-cache

WORKDIR /var/scalargis/scalargis
