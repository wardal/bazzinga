FROM python:3.9-slim
LABEL maintainer="Igor Dubovik"

ENV WORKDIR="/opt/app/bazinga/" \
    PYTHONUNBUFFERED=1
WORKDIR $WORKDIR

ARG REQUIREMENTS_FILE=requirements/base.txt

RUN set -xe \
    && apt-get update --quiet \
    && apt-get install --no-install-recommends --no-install-suggests --quiet --yes \
       gcc python3-dev libpq-dev ca-certificates vim nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ${REQUIREMENTS_FILE} ${REQUIREMENTS_FILE}

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

COPY . .


