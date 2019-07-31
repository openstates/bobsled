#!/bin/sh
set -e

docker build -t jamesturk/bobsled-forever -f Dockerfile.forever .
docker push jamesturk/bobsled-forever
