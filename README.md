# bobsled

bobsled is a task runner designed for Open States

the goal is to make it as cheap and simple as possible to run scrapers
(and other tasks) within the AWS environment

## getting started

* Create a S3 bucket (i.e. bobsled-tutorial), this will be used for uploads and storing your secret config variables.
* Create a second S3 bucket (i.e. status.example.com), this will be used for hosting the public bobsled status logs.
* Create an EC2 key named bobsled (configurable w/ ECS_KEY_NAME)
* Create a VPC (if you don't already have one) and choose a subnet ID to use for launching bobsled instances.
* copy example_zappa_settings.json to zappa_settings.json, set the following
    * s3_bucket - the name of the bucket you just created
    * environment_variables.BOBSLED_STATUS_BUCKET - name of status bucket created above
    * environment_variables.BOBSLED_CONFIG_PATH - e.g. s3://{s3_bucket}/config.yml
    * environment_variables.BOBSLED_SUBNET_ID - e.g. subnet-88eeff00
    * environment_variables.BOBSLED_SECURITY_GROUP_ID - e.g. sg-123456ef
* $ zappa publish dev
* $ aws s3 cp config.yaml BOBSLED_CONFIG_PATH
* $ bobsled init

## optional

CLUSTER_NAME - ECS cluster name. (default: bobsled)
TASK_NAME - ECS task name. (default: bobsled)
LOG_GROUP - CloudWatch log name. (default: bobsled)
ECS_IMAGE_ID - ECS image ID. (defaults to ami-275ffe31, latest ECS AMI)
ECS_KEY_NAME - ECS instance SSH key. (default: bobsled)

GITHUB_USER
GITHUB_KEY
GITHUB_TASK_REPO
GITHUB_ISSUE_REPO
LAMBDA_ARN

## status

at the moment this is experimental and unsupported, use 100% at your own risk
and keep an eye on your EC2 bill as some of the commands may cost you

designed to work within AWS Lambda's Python 3.6 environment

## architecture

* docker images - currently outside the purview of bamboo, but at least one image is needed
* ECS Tasks - one per type of job, consist of a docker image, a command, and optional environment details
* CloudWatch Rule - these are essentially cron jobs that run Lambda tasks
* Lambda Entrypoint - currently a single entrypoint that exists as glue between CloudWatch rules & ECS tasks
* ECS Cluster - group of 1 or more EC2 instances configured to run docker images
* CloudWatch Logs - ECS Cluster nodes are configured to write docker logs to CloudWatch

![](bobsled.png)
