# bobsled

bobsled is a task runner designed for Open States

the goal is to make it as cheap and simple as possible to run scrapers
(and other tasks) within the AWS environment

## status

at the moment this is experimental and unsupported, use 100% at your own risk
and keep an eye on your EC2 bill as some of the commands may cost you

designed to work within AWS Lambda which only supports Python 2.7

## architecture

* docker images - currently outside the purview of bamboo, but at least one image is needed
* ECS tasks - one per type of job, consist of a docker image, a command, and optional environment details
* CloudWatch rule - these are essentially cron jobs that run Lambda tasks
* Lambda entrypoint - currently a single entrypoint that exists as glue between CloudWatch rules & ECS tasks

![](bobsled.png)
