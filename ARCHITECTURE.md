## Settings

environment_service: 

## Interfaces

EnvironmentStorage
  get_environments() -> List[Environment]
  get_environment(name: str) -> Environment


TaskStorage
  get_tasks() -> List[Task]
  get_task(name: str) -> Task


RunService
  cleanup()
  run_task(Task) -> Run
  update_status(Run)
  get_logs(Run) -> str
  get_run(run_id: str) -> Run
  get_runs(*, status: Status, task_name: str, update_status: bool) -> List[Run]
