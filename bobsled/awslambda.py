import os
import glob
import zipfile
import boto3


def bobsled_to_zip():
    # TODO: pip install module-name -t /path/to/project-dir
    basedir = os.path.basename(os.path.dirname(__file__))
    with zipfile.ZipFile('/tmp/bobsled.zip', 'w') as zf:
        filenames = glob.glob(basedir + '/*') + glob.glob(basedir + '/*/*')
        for filename in filenames:
            if not filename.endswith('.pyc'):
                print(filename)
                zf.write(filename, 'bobsled/' + filename)


def publish_function(name, description, timeout=3, delete_first=False):
    lamb = boto3.client('lambda', region_name='us-east-1')

    bobsled_to_zip()

    if delete_first:
        lamb.delete_function(FunctionName=name)
    lamb.create_function(FunctionName=name,
                         Runtime='python2.7',
                         Role='arn:aws:iam::189670762819:role/lambda-ecs-cron',
                         Handler='bobsled.lambda_handlers.test',
                         Code={'ZipFile': open('/tmp/bobsled.zip', 'rb').read()},
                         Description=description,
                         Timeout=timeout,
                         Publish=True)

publish_function('test', 'lambda zip test', delete_first=True)
