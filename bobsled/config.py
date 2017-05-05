import os

CLUSTER_NAME = os.environ.get('BOBSLED_CLUSTER_NAME', 'bobsled')
TASK_NAME = os.environ.get('BOBSLED_TASK_NAME', 'bobsled')
ECS_IMAGE_ID = os.environ.get('BOBSLED_ECS_IMAGE_ID', 'ami-275ffe31')
