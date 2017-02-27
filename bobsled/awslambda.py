import os
import shutil
import zipfile
import tempfile

import boto3


def bobsled_to_zip(zipfilename):
    tmpdir = tempfile.mkdtemp()
    dirname = os.path.dirname(os.path.dirname(__file__))
    os.system('pip install {} -t {}'.format(dirname, tmpdir))

    with zipfile.ZipFile(zipfilename, 'w') as zf:
        filenames = reduce(lambda x, y: x+y,
                           ([os.path.join(d, f) for f in files]
                           for d, _, files in os.walk(tmpdir)))
        for filename in filenames:
            if not filename.endswith('.pyc'):
                afilename = filename.replace(tmpdir + '/', '')
                print(afilename)
                zf.write(filename, afilename)

    shutil.rmtree(tmpdir)


def publish_function(name, description, timeout=3, delete_first=False):
    lamb = boto3.client('lambda', region_name='us-east-1')

    zipfilename = '/tmp/bobsled.zip'

    bobsled_to_zip(zipfilename)

    if delete_first:
        lamb.delete_function(FunctionName=name)
    lamb.create_function(FunctionName=name,
                         Runtime='python2.7',
                         Role='arn:aws:iam::189670762819:role/lambda-ecs-cron',
                         Handler='bobsled.lambda_handlers.test',
                         Code={'ZipFile': open(zipfilename, 'rb').read()},
                         Description=description,
                         Timeout=timeout,
                         Publish=True)

if __name__ == '__main__':
    publish_function('bobsled', 'bobsled lambda zip test', delete_first=True)
