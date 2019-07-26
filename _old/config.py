import os

# optional (have defaults)
CLUSTER_NAME = os.environ.get('BOBSLED_CLUSTER_NAME', 'bobsled-fg')
TASK_NAME = os.environ.get('BOBSLED_TASK_NAME', 'bobsled')
LOG_GROUP = os.environ.get('BOBSLED_ECS_LOG_GROUP', 'bobsled')
ECS_IMAGE_ID = os.environ.get('BOBSLED_ECS_IMAGE_ID', 'ami-275ffe31')
ECS_KEY_NAME = os.environ.get('BOBSLED_ECS_KEY_NAME', 'bobsled')

# required
SUBNET_ID = os.environ.get('BOBSLED_SUBNET_ID')
SECURITY_GROUP_ID = os.environ.get('BOBSLED_SECURITY_GROUP_ID')
CONFIG_PATH = os.environ.get('BOBSLED_CONFIG_PATH')
STATUS_BUCKET = os.environ.get('BOBSLED_STATUS_BUCKET')

# required for GitHub features
GITHUB_USER = os.environ.get('BOBSLED_GITHUB_USER')
GITHUB_KEY = os.environ.get('BOBSLED_GITHUB_KEY')
GITHUB_TASK_REPO = os.environ.get('BOBSLED_GITHUB_TASK_REPO')
GITHUB_ISSUE_REPO = os.environ.get('BOBSLED_GITHUB_ISSUE_REPO')

# ???
LAMBDA_ARN = os.environ.get('BOBSLED_LAMBDA_ARN')
