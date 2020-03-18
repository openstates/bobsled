#!/bin/bash 

PGHOST=localhost PGPORT=5435 PGUSER=bobsled PGPASSWORD=bobsled psql -c 'drop database bobsled_test;'
PGHOST=localhost PGPORT=5435 PGUSER=bobsled PGPASSWORD=bobsled psql -c 'create database bobsled_test;'
BOTO_CONFIG=/dev/null AWS_DEFAULT_REGION=us-east-1 BOBSLED_SECRET_KEY="secret-stuff-here" BOBSLED_TASKS_FILENAME="bobsled/tests/tasks/tasks.yml" poetry run pytest $@
