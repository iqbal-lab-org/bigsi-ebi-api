FROM python:3.6-slim-buster AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc
RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt && pip install uWSGI==2.0.18

FROM python:3.6-slim-buster AS build-image
COPY --from=compile-image /opt/venv /opt/venv

RUN mkdir /bigsi-aggregator
WORKDIR /bigsi-aggregator
ADD . /bigsi-aggregator/

ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"
EXPOSE 8001

CMD uwsgi --http :80 --harakiri 300  --buffer-size=65535 --protocol=http -w wsgi

