# bobsled

[![Build Status](https://travis-ci.com/jamesturk/bobsled.svg?branch=master)](https://travis-ci.com/jamesturk/bobsled)

bobsled is a task runner, originally designed for [Open States](https://openstates.org)

The project makes it easy to run one-off and scheduled tasks in Docker, including Amazon ECS.


## Configuration

Required Settings:
  - BOBSLED_SECRET_KEY

Provider Settings:
  - BOBSLED_ENV_PROVIDER (*LocalEnvironmentProvider*, )
  - BOBSLED_STORAGE_PROVIDER (*InMemoryStorage, DatabaseStorage)
  - BOBSLED_TASK_PROVIDER (*YamlTaskProvider*)
  - BOBSLED_RUNNER (*LocalRunService, ECSRunService)

Callback Settings:
  - BOBSLED_ENABLE_GITHUB_ISSUE_CALLBACK

DatabaseStorage Settings:
  - BOBSLED_DATABASE_URI

YamlTaskProvider Settings:
  - BOBSLED_TASKS_FILENAME
  - BOBSLED_TASKS_GITHUB_USER
  - BOBSLED_TASKS_GITHUB_REPO
  - BOBSLED_TASKS_DIRNAME
  - BOBSLED_GITHUB_API_KEY

ECSRunService Settings:
  - BOBSLED_ECS_CLUSTER
  - BOBSLED_SUBNET_ID
  - BOBSLED_SECURITY_GROUP_ID
  - BOBSLED_LOG_GROUP
  - BOBSLED_ROLE_ARN

YamlEnvironmentProvider Settings:
  - BOBSLED_ENVIRONMENT_FILENAME

LocalEnvironmentProvider Settings:
  -  BOBSLED_ENVIRONMENT_JSON

ParamstoreEnvironmentProvider Settings:
  - BOBSLED_ENVIRONMENT_PARAMSTORE_PREFIX

GitHub Callback Settings:
  - BOBSLED_GITHUB_API_KEY
  - BOBSLED_GITHUB_ISSUE_USER
  - BOBSLED_GITHUB_ISSUE_REPO

