# bobsled

bobsled is a task runner, originally designed for [Open States](https://openstates.org)

The project makes it easy to run one-off and scheduled tasks in Docker, including Amazon ECS.

## Configuration

Provider Settings:

- BOBSLED_RUNNER (\*LocalRunService, ECSRunService)

TaskProvider Settings:

- BOBSLED_TASKS_FILENAME
- BOBSLED_TASKS_DIRNAME

ECSRunService Settings:

- BOBSLED_ECS_CLUSTER
- BOBSLED_SUBNET_ID
- BOBSLED_SECURITY_GROUP_ID
- BOBSLED_LOG_GROUP
- BOBSLED_ROLE_ARN

EnvironmentProvider Settings:

- BOBSLED_ENVIRONMENT_FILENAME
- BOBSLED_ENVIRONMENT_DIRNAME
