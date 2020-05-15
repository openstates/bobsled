#!/bin/bash 

set ARGS = $@

PGHOST=localhost PGUSER=bobsled PGPASSWORD=bobsled psql -c 'drop database bobsled_test;'
PGHOST=localhost PGUSER=bobsled PGPASSWORD=bobsled psql -c 'create database bobsled_test;'
export BOTO_CONFIG=/dev/null
export AWS_DEFAULT_REGION=us-east-1
export BOBSLED_SECRET_KEY="secret-stuff-here"
export BOBSLED_TASKS_FILENAME="bobsled/tests/tasks/tasks.yml"
export BOBSLED_ENVIRONMENT_FILENAME="bobsled/tests/environments.yml"
poetry run pytest $ARGS
