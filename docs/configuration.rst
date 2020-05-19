Configuration
=============

Environment Variables
----------------------

Required
~~~~~~~~

These environment variables are required.

``BOBSLED_SECRET_KEY`` 
  Set to a random string that is not publicly known, used for token signing.

``BOBSLED_TASKS_FILENAME`` or ``BOBSLED_TASKS_DIRNAME``
  Either the name of a file (tasks.yml) or the name of a directory containing multiple yml files defining the tasks.

  See :ref:`loading yaml` for details.

``BOBSLED_ENVIRONMENT_FILENAME`` or ``BOBSLED_ENVIRONMENT_DIRNAME``
  Either the name of a file (tasks.yml) or the name of a directory containing multiple yml files defining the environments.
  
  See :ref:`loading yaml` for details.

Storage
~~~~~~~~

``BOBSLED_STORAGE``
  There are two storage providers available, the default 'InMemoryStorage', and 'DatabaseStorage'.
``BOBSLED_DATABASE_URI``
  If using DatabaseStorage, this environment variable must be set to a Postgres URI.

Run Services
~~~~~~~~~~~~

``BOBSLED_RUNNER``
  There are two run services provided, the default 'LocalRunService', and 'ECSRunService'.
``BOBSLED_ECS_CLUSTER``
  AWS ECS Cluster name
``BOBSLED_SUBNET_ID``
  AWS Subnet ID for jobs (e.g. subnet-86abcdef)
``BOBSLED_SECURITY_GROUP_ID``
  AWS Security Group ID for jobs (e.g. sg-70123456)
``BOBSLED_LOG_GROUP``
  AWS Log Group Name for CloudWatch logs
``BOBSLED_ROLE_ARN``
  AWS Task Role ARN for jobs (e.g. arn:aws:iam::1234567890:role/ecs-fargate-bobsled')

Beat
~~~~

``BOBSLED_BEAT_HOSTNAME``
  Hostname of the machine that the bobsled.beat daemon is running on.
``BOBSLED_BEAT_PORT``
  Port that the beat daemon is running on (default: 1988).

GitHub Settings
~~~~~~~~~~~~~~~

``BOBSLED_GITHUB_API_KEY``
  GitHub API Key with permission to read the configuration repo if one is being used.
  If the GitHub issue callback is enabled, the key should also have the issues permissions.
``BOBSLED_CONFIG_GITHUB_USER``
  Username for repository where task/environment configuration is stored.
``BOBSLED_CONFIG_GITHUB_REPO``
  Repository name for repository where task/environment configuration is stored.


GitHub Issue Creation
~~~~~~~~~~~~~~~~~~~~~

``BOBSLED_ENABLE_GITHUB_ISSUE_CALLBACK``
  Set to true to enable creation of GitHub issues when jobs fail.
``BOBSLED_GITHUB_ISSUE_USER``
  Username for repository where GitHub issues will be created.
``BOBSLED_GITHUB_ISSUE_REPO``
  Repository name for repository where GitHub issues will be created.


.. _loading yaml:

YAML Configuration
------------------

Because it is important to be able to change them without a restart, tasks & environment config come from YAML files.

They are read from YAML files as defined by the BOBSLED_TASKS_* and BOBSLED_ENVIRONMENT_* settings.

There are a few different cases to consider:

* **Local YAML, single file** - the simplest case, just set BOBSLED_TASKS_FILENAME and BOBSLED_ENVIRONMENT_FILENAME to the absolute path to the YAML.
* **GitHub YAML, single file** - if you'd like to read a file that is stored in a GitHub repo, set the BOBSLED_CONFIG_GITHUB_USER, and BOBSLED_CONFIG_GITHUB_REPO and the filename will be interpreted as relative to the repository root.
* **GitHub YAML, many files** - in this case, you'd set the GitHub settings just as above but specify a directory name instead.  All of the .yml files in that directory will be read as the tasks/environment respectively.

