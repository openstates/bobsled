from bobsled2.yaml_environment import YamlEnvironment
from bobsled2.yaml_tasks import YamlTasks
from bobsled2.local_run_service import LocalRunService

ENVIRONMENT_SERVICE = YamlEnvironment("bobsled2/tests/testenv.yml")
TASK_SERVICE = YamlTasks("bobsled2/tests/tasks.yml")
RUN_SERVICE = LocalRunService()
