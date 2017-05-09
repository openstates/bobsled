import os

# optional (have defaults)
CLUSTER_NAME = os.environ.get('BOBSLED_CLUSTER_NAME', 'bobsled')
TASK_NAME = os.environ.get('BOBSLED_TASK_NAME', 'bobsled')
LOG_GROUP = os.environ.get('BOBSLED_ECS_LOG_GROUP', 'bobsled')
ECS_IMAGE_ID = os.environ.get('BOBSLED_ECS_IMAGE_ID', 'ami-275ffe31')
ECS_KEY_NAME = os.environ.get('BOBSLED_ECS_KEY_NAME', 'bobsled.pub')
SECURITY_GROUP_ID = os.environ.get('BOBSLED_SECURITY_GROUP_ID', 'bobsled')

# required
STATUS_BUCKET = os.environ['BOBSLED_STATUS_BUCKET']
GITHUB_USER = os.environ['BOBSLED_GITHUB_USER']
GITHUB_KEY = os.environ['BOBSLED_GITHUB_KEY']
GITHUB_TASK_REPO = os.environ['BOBSLED_GITHUB_TASK_REPO']
GITHUB_ISSUE_REPO = os.environ['BOBSLED_GITHUB_ISSUE_REPO']

# ???
CONFIG_BUCKET = os.environ['BOBSLED_CONFIG_BUCKET']
