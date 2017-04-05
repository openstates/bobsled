from __future__ import print_function
import os
from jinja2 import Environment, PackageLoader
import boto3
from .utils import all_files


def format_datetime(value):
    return value.strftime('%m/%d %H:%M:%S')


def format_time(value):
    return value.strftime('%H:%M:%S')


def render_jinja_template(template, **context):
    env = Environment(loader=PackageLoader('bobsled', 'templates'))
    env.filters['datetime'] = format_datetime
    env.filters['time'] = format_time
    template = env.get_template(template)
    return template.render(**context)


def upload(dirname):
    s3 = boto3.resource('s3')
    CONTENT_TYPE = {'html': 'text/html',
                    'css': 'text/css'}

    for filename in all_files(dirname):
        ext = filename.rsplit('.', 1)[-1]
        content_type = CONTENT_TYPE.get(ext, '')
        s3.meta.client.put_object(
            ACL='public-read',
            Body=open(filename),
            Bucket=os.environ['BOBSLED_STATUS_BUCKET'],
            Key=filename.replace(dirname + '/', ''),
            ContentType=content_type,
        )
