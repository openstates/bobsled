# bobsled

[![Build Status](https://travis-ci.com/stateautomata/bobsled.svg?branch=master)](https://travis-ci.com/stateautomata/bobsled)

bobsled is a task runner, originally designed for [Open States](https://openstates.org)

The project makes it easy to run one-off and scheduled tasks in Docker, including Amazon ECS.

## Configuration

Required Settings:

- BOBSLED_SECRET_KEY

Beat Settings:

- BOBSLED_BEAT_HOSTNAME
- BOBSLED_BEAT_PORT

Provider Settings:

- BOBSLED_STORAGE (\*InMemoryStorage, DatabaseStorage)
- BOBSLED_RUNNER (\*LocalRunService, ECSRunService)

Callback Settings:

- BOBSLED_ENABLE_GITHUB_ISSUE_CALLBACK

DatabaseStorage Settings:

- BOBSLED_DATABASE_URI

TaskProvider Settings:

- BOBSLED_TASKS_FILENAME
- BOBSLED_TASKS_DIRNAME
- BOBSLED_CONFIG_GITHUB_USER
- BOBSLED_CONFIG_GITHUB_REPO
- BOBSLED_GITHUB_API_KEY

ECSRunService Settings:

- BOBSLED_ECS_CLUSTER
- BOBSLED_SUBNET_ID
- BOBSLED_SECURITY_GROUP_ID
- BOBSLED_LOG_GROUP
- BOBSLED_ROLE_ARN

EnvironmentProvider Settings:

- BOBSLED_ENVIRONMENT_FILENAME
- BOBSLED_ENVIRONMENT_DIRNAME
- BOBSLED_CONFIG_GITHUB_USER
- BOBSLED_CONFIG_GITHUB_REPO
- BOBSLED_GITHUB_API_KEY

GitHub Callback Settings:

- BOBSLED_GITHUB_API_KEY
- BOBSLED_GITHUB_ISSUE_USER
- BOBSLED_GITHUB_ISSUE_REPO
