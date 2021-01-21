ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}python:3.8-alpine

RUN apk add --no-cache git openssh knot

RUN mkdir -p /zones /rundir/knot/

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/usr/src/app/entrypoint.sh"]
